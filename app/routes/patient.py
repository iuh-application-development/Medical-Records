from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from app.models.user import User
from app.models.medical_record import MedicalRecord, Notification
from app.forms import UpdateProfileForm, MedicalRecordForm
from app import db, s
import os
from werkzeug.utils import secure_filename
import pandas as pd
import json
import plotly.express as px
from datetime import datetime

bp = Blueprint('patient', __name__)

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateProfileForm()
    if form.validate_on_submit():
        try:
            if form.avatar.data:
                file = form.avatar.data
                filename = secure_filename(file.filename)
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
                    os.makedirs(current_app.config['UPLOAD_FOLDER'])
                file.save(file_path)
                current_user.avatar = filename
            
            current_user.full_name = form.full_name.data
            current_user.phone = form.phone.data
            current_user.email = form.email.data
            db.session.commit()
            flash('Your profile has been updated successfully!', 'success')
            return redirect(url_for('patient.profile'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating your profile.', 'danger')
    
    elif request.method == 'GET':
        form.full_name.data = current_user.full_name
        form.phone.data = current_user.phone
        form.email.data = current_user.email
    
    return render_template('profile.html', form=form)

@bp.route('/new_record', methods=['GET', 'POST'])
@login_required
def new_record():
    if current_user.role != 'patient':
        flash('Only patients can create medical records.', 'danger')
        return redirect(url_for('index'))
    
    form = MedicalRecordForm()
    if form.validate_on_submit():
        record = MedicalRecord(
            patient_id=current_user.id,
            date=form.date.data,
            hgb=form.hgb.data,
            rbc=form.rbc.data,
            wbc=form.wbc.data,
            plt=form.plt.data,
            hct=form.hct.data,
            glucose=form.glucose.data,
            creatinine=form.creatinine.data,
            alt=form.alt.data,
            cholesterol=form.cholesterol.data,
            crp=form.crp.data
        )
        db.session.add(record)
        db.session.commit()
        flash('Medical record has been added!', 'success')
        return redirect(url_for('patient.view_records'))
    return render_template('new_record.html', form=form)

@bp.route('/view_records')
@login_required
def view_records():
    if current_user.role != 'patient':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    records = MedicalRecord.query.filter_by(patient_id=current_user.id).order_by(MedicalRecord.date.desc()).all()
    return render_template('view_records.html', records=records, patient=current_user, patient_id=current_user.id)

@bp.route('/view_charts')
@login_required
def view_charts():
    if current_user.role != 'patient':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    # Get selected parameters from request
    selected_parameters = request.args.getlist('parameters')
    all_parameters = ['hgb', 'rbc', 'wbc', 'plt', 'hct', 'glucose', 'creatinine', 'alt', 'cholesterol', 'crp']
    
    # If no parameters selected, show all
    if not selected_parameters:
        selected_parameters = all_parameters
    
    # Get patient's records
    records = MedicalRecord.query.filter_by(patient_id=current_user.id).order_by(MedicalRecord.date).all()
    
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
            'crp': float(record.crp) if record.crp else None
        }
        data.append(record_data)
    
    # Create charts
    charts = {}
    if data:
        df = pd.DataFrame(data)
        
        for param in selected_parameters:
            if param in df.columns:
                param_df = df[df[param].notnull()]
                if not param_df.empty:
                    fig = px.line(param_df, x='date', y=param, title=f'{param.upper()} Over Time')
                    fig.update_layout(
                        xaxis_title='Date',
                        yaxis_title=param.upper(),
                        showlegend=True,
                        height=400,
                        margin=dict(l=50, r=50, t=50, b=50)
                    )
                    fig.update_traces(
                        line=dict(width=2),
                        mode='lines+markers',
                        marker=dict(size=8)
                    )
                    fig_dict = fig.to_dict()
                    for trace in fig_dict['data']:
                        for key, value in trace.items():
                            if hasattr(value, 'tolist'):
                                trace[key] = value.tolist()
                    charts[param] = json.dumps(fig_dict)
    
    return render_template('view_charts.html', charts=charts, parameters=selected_parameters)

@bp.route('/notifications')
@login_required
def notifications():
    if current_user.role != 'patient':
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    # Fetch all notifications for the current patient, ordered by date descending
    # We'll show both read and unread notifications, but style them differently in the template
    user_notifications = Notification.query.filter_by(patient_id=current_user.id)\
                                      .order_by(Notification.date.desc()).all()
                                        
    return render_template('notifications.html', notifications=user_notifications)

# Add a route to mark a notification as read (Example)
@bp.route('/notifications/mark_read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_as_read(notification_id):
    if current_user.role != 'patient':
        return jsonify({'error': 'Access denied'}), 403
        
    notification = Notification.query.get_or_404(notification_id)
    
    # Ensure the notification belongs to the current user
    if notification.patient_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    notification.read = True
    try:
        db.session.commit()
        return jsonify({'success': True}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error marking notification as read: {e}")
        return jsonify({'error': 'Could not update notification status'}), 500

@bp.route('/notifications/delete/<int:notification_id>', methods=['POST'])
@login_required
def delete_notification(notification_id):
    if current_user.role != 'patient':
        return jsonify({'error': 'Access denied'}), 403
        
    notification = Notification.query.get_or_404(notification_id)
    
    # Ensure the notification belongs to the current user
    if notification.patient_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
        
    try:
        db.session.delete(notification)
        db.session.commit()
        return jsonify({'success': True}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting notification: {e}")
        return jsonify({'error': 'Could not delete notification'}), 500

@bp.route('/api/unread-notifications-count')
@login_required
def unread_notifications_count():
    """API endpoint để trả về số lượng thông báo chưa đọc"""
    if current_user.role != 'patient':
        return jsonify({'count': 0})
    
    count = Notification.query.filter_by(patient_id=current_user.id, read=False).count()
    return jsonify({'count': count})

@bp.route('/view_doctors')
@login_required
def view_doctors():
    """Route để bệnh nhân xem danh sách các bác sĩ"""
    if current_user.role != 'patient':
        flash('Access denied. Patients only.', 'danger')
        return redirect(url_for('index'))
    
    # Lấy danh sách tất cả bác sĩ
    doctors = User.query.filter_by(role='doctor').all()
    return render_template('view_doctors.html', doctors=doctors)