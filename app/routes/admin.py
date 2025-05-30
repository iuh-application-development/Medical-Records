from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app.models.user import User
from app.models.medical_record import MedicalRecord
from app.forms.admin_forms import AdminUserManagementForm, AdminPasswordResetForm 
from app import db, s
import pandas as pd
import io

bp = Blueprint('admin', __name__)

@bp.route('/users')
@login_required
def users():
    if current_user.role != 'admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('index'))
    
    users = User.query.all()
    role_form = AdminUserManagementForm()
    password_form = AdminPasswordResetForm()
    return render_template('admin_users.html', users=users, role_form=role_form, password_form=password_form)

@bp.route('/update_role/<int:user_id>', methods=['POST'])
@login_required
def update_role(user_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('index'))
    
    form = AdminUserManagementForm()
    user = User.query.get_or_404(user_id)
    
    # Set the current role in the form
    form.current_role.data = user.role
    
    if form.validate_on_submit():
        new_role = form.role.data
        
        # Check if the user is trying to change their own role
        if user.id == current_user.id:
            flash('Cannot change your own role.', 'danger')
            return redirect(url_for('admin.users'))
        
        if user.role != new_role:
            user.role = new_role
            db.session.commit()
            flash(f'Successfully updated {user.username}\'s role to {new_role}', 'success')
        else:
            flash(f'No role change needed - {user.username} is already a {new_role}', 'info')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'danger')
    
    return redirect(url_for('admin.users'))

@bp.route('/reset_password/<int:user_id>', methods=['POST'])
@login_required
def reset_password(user_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('index'))
    
    if not request.form.get('csrf_token'):
        flash('Invalid CSRF token. Please try again.', 'danger')
        return redirect(url_for('admin.users'))

    user = User.query.get_or_404(user_id)
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not new_password or not confirm_password:
        flash('Both password fields are required.', 'danger')
        return redirect(url_for('admin.users'))

    if new_password != confirm_password:
        flash('Passwords do not match.', 'danger')
        return redirect(url_for('admin.users'))

    try:
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        flash(f'Password for user {user.username} has been reset successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while resetting the password. Please try again.', 'danger')

    return redirect(url_for('admin.users'))

@bp.route('/manage_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def manage_user(user_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    form = AdminUserManagementForm()
    
    if request.method == 'GET':
        form.current_role.data = user.role
        form.role.data = user.role
    
    if form.validate_on_submit():
        if user.role != form.role.data:
            user.role = form.role.data
            db.session.commit()
            flash(f'User role updated successfully to {form.role.data}.', 'success')
            return redirect(url_for('admin.users'))
    
    return render_template('manage_user.html', form=form, user=user)

@bp.route('/users/export')
@login_required
def export_users():
    if current_user.role != 'admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('index'))
    
    # Lấy tất cả user
    users = User.query.all()
    
    # Tạo DataFrame
    data = []
    for user in users:
        data.append({
            'ID': user.id,
            'Username': user.username,
            'Email': user.email,
            'Phone': user.phone,
            'Role': user.role,
            'Created At': user.created_at
        })
    df = pd.DataFrame(data)
    
    # Tạo file Excel trong memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Users', index=False)
    
    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='users.xlsx'
    )

@bp.route('/records/export')
@login_required
def export_records():
    if current_user.role != 'admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('index'))
    
    # Lấy tất cả bản ghi y tế
    records = MedicalRecord.query.all()
    
    # Tạo DataFrame
    data = []
    for record in records:
        data.append({
            'ID': record.id,
            'Patient ID': record.patient_id,
            'Date': record.date,
            'HGB': record.hgb,
            'RBC': record.rbc,
            'WBC': record.wbc,
            'PLT': record.plt,
            'HCT': record.hct,
            'Glucose': record.glucose,
            'Creatinine': record.creatinine,
            'ALT': record.alt,
            'Cholesterol': record.cholesterol,
            'CRP': record.crp,
            'Created At': record.created_at
        })
    df = pd.DataFrame(data)
    
    # Tạo file Excel trong memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Medical Records', index=False)
    
    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='medical_records.xlsx'
    )