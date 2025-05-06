from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, make_response
from flask_login import login_required, current_user
from app.models.user import User
from app.models.medical_record import MedicalRecord, Notification
from app.forms import NotificationForm
from app import db, s, csrf
import pandas as pd
from datetime import datetime
import json
import plotly.express as px

bp = Blueprint('doctor', __name__)

@bp.route('/search_patient')
@login_required
def search_patient():
    if current_user.role != 'doctor':
        flash('Access denied. Doctors only.', 'danger')
        return redirect(url_for('index'))
    
    patients = User.query.filter_by(role='patient').all()
    return render_template('search_patient.html', patients=patients)

@bp.route('/view_patient_records/<int:patient_id>')
@login_required
def view_patient_records(patient_id):
    if current_user.role != 'doctor':
        flash('Access denied. Doctors only.', 'danger')
        return redirect(url_for('index'))
    
    patient = User.query.get_or_404(patient_id)
    records = MedicalRecord.query.filter_by(patient_id=patient_id).order_by(MedicalRecord.date.desc()).all()
    notification_form = NotificationForm()
    return render_template('view_records.html', records=records, patient=patient, notification_form=notification_form, patient_id=patient_id)

@bp.route('/view_charts')  
@login_required
def view_charts():
    # Get patient_id from query parameters
    patient_id = request.args.get('patient_id')
    
    # Get records based on role and patient_id
    if current_user.role == 'patient':
        records = MedicalRecord.query.filter_by(patient_id=current_user.id).order_by(MedicalRecord.date).all()
    else:  # Doctor role
        if patient_id:
            records = MedicalRecord.query.filter_by(patient_id=patient_id).order_by(MedicalRecord.date).all()
            patient = User.query.get_or_404(patient_id)
        else:
            records = MedicalRecord.query.order_by(MedicalRecord.date).all()
    
    # Get selected parameters from request
    selected_parameters = request.args.getlist('parameters')
    all_parameters = ['hgb', 'rbc', 'wbc', 'plt', 'hct', 'glucose', 'creatinine', 'alt', 'cholesterol', 'crp']
    
    # If no parameters selected, show all
    if not selected_parameters:
        selected_parameters = all_parameters
    
    # Convert records to pandas DataFrame for easier manipulation
    data = []
    for record in records:
        record_data = {
            'date': record.date.strftime('%Y-%m-%d'),
            'hgb': float(record.hgb) if record.hgb else None,
            'rbc': float(record.rbc) if record.rbc else None,
            'wbc': float(record.wbc) if record.wbc else None,
            'plt': float(record.plt) if record.plt else None,
            'hct': float(record.hct) if record.hct else None,
            'glucose': float(record.glucose) if record.glucose else None,
            'creatinine': float(record.creatinine) if record.creatinine else None,
            'alt': float(record.alt) if record.alt else None,
            'cholesterol': float(record.cholesterol) if record.cholesterol else None,
            'crp': float(record.crp) if record.crp else None,
            'patient_id': record.patient_id
        }
        data.append(record_data)
    
    # Create DataFrame only if we have data
    charts = {}
    if data:
        df = pd.DataFrame(data)
        
        # Create charts for selected parameters
        for param in selected_parameters:
            if param in df.columns:  # Check if parameter exists in DataFrame
                # Filter out records with null values for the current parameter
                param_df = df[df[param].notnull()]
                if not param_df.empty:
                    fig = px.line(param_df, x='date', y=param, title=f'{param.upper()} Over Time')
                    fig.update_layout(
                        xaxis_title='Date',
                        yaxis_title=param.upper(),
                        showlegend=True,
                        height=400,  # Set a fixed height for better layout
                        margin=dict(l=50, r=50, t=50, b=50)  # Add margins for better spacing
                    )
                    # Update line style and add markers
                    fig.update_traces(
                        line=dict(width=2),
                        mode='lines+markers',
                        marker=dict(size=8)
                    )
                    # Convert numpy arrays to lists for JSON serialization
                    fig_dict = fig.to_dict()
                    for trace in fig_dict['data']:
                        for key, value in trace.items():
                            if hasattr(value, 'tolist'):
                                trace[key] = value.tolist()
                    charts[param] = json.dumps(fig_dict)
    
    # Pass patient info to template if doctor is viewing specific patient
    if current_user.role == 'doctor' and patient_id:
        return render_template('view_charts.html', charts=charts, parameters=selected_parameters, patient=patient)
    return render_template('view_charts.html', charts=charts, parameters=selected_parameters)

@bp.route('/send_notification/<int:patient_id>', methods=['POST'])  # Changed from @app.route
@login_required
def send_notification(patient_id):
    if current_user.role not in ['doctor', 'admin']:
        return jsonify({
            'success': False,
            'message': 'Access denied. Doctors and admin only.'
        }), 403
    
    patient = User.query.get_or_404(patient_id)
    message = request.form.get('message')
    
    if not message:
        return jsonify({
            'success': False,
            'message': 'Message cannot be empty.'
        }), 400
        
    try:
        notification = Notification(
            patient_id=patient_id,
            doctor_id=current_user.id,
            message=message,
            date=datetime.utcnow(),
            read=False
        )
        db.session.add(notification)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Notification sent to {patient.username} successfully!'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Failed to send notification. Please try again.'
        }), 500

@bp.route('/download_records/<int:patient_id>')  # Changed from @app.route
@login_required
def download_records(patient_id):
    if current_user.role != 'doctor':
        flash('Access denied. Doctors only.', 'danger')
        return redirect(url_for('index'))
    
    patient = User.query.get_or_404(patient_id)
    records = MedicalRecord.query.filter_by(patient_id=patient_id).order_by(MedicalRecord.date.desc()).all()
    
    # Create CSV data
    data = []
    for record in records:
        data.append({
            'Date': record.date.strftime('%Y-%m-%d'),
            'HGB': record.hgb,
            'RBC': record.rbc,
            'WBC': record.wbc,
            'PLT': record.plt,
            'HCT': record.hct,
            'Glucose': record.glucose,
            'Creatinine': record.creatinine,
            'ALT': record.alt,
            'Cholesterol': record.cholesterol,
            'CRP': record.crp
        })
    
    df = pd.DataFrame(data)
    csv_data = df.to_csv(index=False)
    
    # Create response with CSV file
    response = make_response(csv_data)
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename={patient.username}_medical_records.csv'
    
    return response

@bp.route('/start_conversation', methods=['POST'])
@login_required
def start_conversation():
    if current_user.role != 'doctor':
        return jsonify({
            'success': False,
            'message': 'Access denied. Doctors only.'
        }), 403
    
    patient_id = request.form.get('patient_id')
    
    if not patient_id:
        return jsonify({
            'success': False,
            'message': 'Patient ID is required.'
        }), 400
    
    try:
        # Check if patient exists
        patient = User.query.filter_by(id=patient_id, role='patient').first()
        if not patient:
            return jsonify({
                'success': False,
                'message': 'Patient not found.'
            }), 404
        
        # Here you would create or retrieve an existing conversation
        # This is a placeholder - you need to implement your conversation logic
        # For example, you might have a Conversation model or use a chat system
        
        # For now, we'll just return a success response with a placeholder conversation ID
        # Replace this with your actual conversation creation/retrieval logic
        conversation_id = patient_id  # Placeholder - replace with actual conversation ID
        
        return jsonify({
            'success': True,
            'conversation_id': conversation_id,
            'message': f'Conversation with {patient.username} started.'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to start conversation: {str(e)}'
        }), 500
