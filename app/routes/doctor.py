from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, make_response
from flask_login import login_required, current_user
from app.models.user import User
from app.models.medical_record import MedicalRecord, Notification
from app.forms import NotificationForm
from app import db, s
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
    return render_template('view_records.html', records=records, patient=patient, notification_form=notification_form)

@bp.route('/view_charts')  # Changed from @app.route
@login_required
def view_charts():
    if current_user.role == 'patient':
        records = MedicalRecord.query.filter_by(patient_id=current_user.id).order_by(MedicalRecord.date).all()
    else:  # Doctor role
        patient_id = request.args.get('patient_id')
        if patient_id:
            records = MedicalRecord.query.filter_by(patient_id=patient_id).order_by(MedicalRecord.date).all()
        else:
            records = MedicalRecord.query.order_by(MedicalRecord.date).all()
    
    # Get selected parameters from request
    selected_parameters = request.args.getlist('parameters')
    all_parameters = ['hgb', 'rbc', 'wbc', 'plt', 'hct', 'glucose', 'creatinine', 'alt', 'cholesterol', 'crp']
    
    # If no parameters selected, show all
    if not selected_parameters:
        selected_parameters = all_parameters
    
    # Convert records to pandas DataFrame for easier manipulation
    data = [{
        'date': record.date.strftime('%Y-%m-%d'),  # Convert datetime to string
        'hgb': record.hgb,
        'rbc': record.rbc,
        'wbc': record.wbc,
        'plt': record.plt,
        'hct': record.hct,
        'glucose': record.glucose,
        'creatinine': record.creatinine,
        'alt': record.alt,
        'cholesterol': record.cholesterol,
        'crp': record.crp,
        'patient_id': record.patient_id
    } for record in records]
    
    df = pd.DataFrame(data)
    
    # Create charts for selected parameters
    charts = {}
    for param in selected_parameters:
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