from flask import Flask, render_template, request, redirect, url_for, flash, send_file, make_response, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from forms import RegistrationForm, LoginForm, UpdateProfileForm, MedicalRecordForm, NotificationForm, ResetPasswordRequestForm, ResetPasswordForm, AdminUserManagementForm, AdminPasswordResetForm
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import pandas as pd
import plotly.express as px
import json
from itsdangerous import URLSafeTimedSerializer
from flask_wtf.csrf import CSRFProtect
import uuid
import random



# Tải biến môi trường từ file .env
load_dotenv()

# Khởi tạo ứng dụng Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI')
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER')
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

csrf = CSRFProtect()
csrf.init_app(app)

db = SQLAlchemy(app)
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
login_manager = LoginManager(app)
login_manager.login_view = 'login'
mail = Mail(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    phone = db.Column(db.String(20))
    full_name = db.Column(db.String(100))
    avatar = db.Column(db.String(200))
    role = db.Column(db.String(20))  # 'patient' or 'doctor'
    records = db.relationship('MedicalRecord', backref='patient', lazy=True)
    notifications = db.relationship('Notification', backref='patient', lazy=True)
    reset_code = db.Column(db.String(6))
    reset_code_expiry = db.Column(db.DateTime)

class MedicalRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    hgb = db.Column(db.Float)
    rbc = db.Column(db.Float)
    wbc = db.Column(db.Float)
    plt = db.Column(db.Float)
    hct = db.Column(db.Float)
    glucose = db.Column(db.Float)
    creatinine = db.Column(db.Float)
    alt = db.Column(db.Float)
    cholesterol = db.Column(db.Float)
    crp = db.Column(db.Float)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists. Please choose a different one.', 'danger')
            return render_template('register.html', form=form)
        if User.query.filter_by(email=form.email.data).first():
            flash('Email address already exists. Please use a different one.', 'danger')
            return render_template('register.html', form=form)
        hashed_password = generate_password_hash(form.password.data)
        user = User(username=form.username.data, email=form.email.data,
                password_hash=hashed_password, phone=form.phone.data,
                role='patient')
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = s.dumps(user.email, salt='reset-password-salt')
            reset_url = url_for('reset_password', token=token, _external=True)
            msg = Message('Password Reset Request',
                        sender=app.config['MAIL_USERNAME'],
                        recipients=[user.email])
            msg.body = f'''To reset your password, visit the following link:
{reset_url}

If you did not make this request, simply ignore this email.
'''
            mail.send(msg)
            flash('Check your email for instructions to reset your password.', 'info')
            return redirect(url_for('login'))
        flash('Email address not found.', 'error')
    return render_template('reset_password_request.html', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    try:
        email = s.loads(token, salt='reset-password-salt', max_age=3600)  # Token expires in 1 hour
    except:
        flash('The password reset link is invalid or has expired.', 'error')
        return redirect(url_for('reset_password_request'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=email).first()
        if user:
            user.password_hash = generate_password_hash(form.password.data)
            db.session.commit()
            flash('Your password has been reset.', 'success')
            return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)

@app.route('/notifications')
@login_required
def notifications():
    if current_user.role == 'patient':
        # Patients can only see notifications sent to them
        notifications = Notification.query.filter_by(patient_id=current_user.id).order_by(Notification.date.desc()).all()
    elif current_user.role == 'doctor':
        # Doctors can only see notifications they sent
        patient_ids = [n.patient_id for n in Notification.query.all()]
        patients = User.query.filter(User.id.in_(patient_ids)).all()
        notifications = []
        for patient in patients:
            patient_notifications = Notification.query.filter_by(patient_id=patient.id).order_by(Notification.date.desc()).all()
            notifications.extend(patient_notifications)
    else:
        flash('Access denied.', 'danger')
        return redirect(url_for('index'))
    
    # Mark notifications as read
    if current_user.role == 'patient':
        for notification in notifications:
            if not notification.read:
                notification.read = True
        db.session.commit()
    
    return render_template('notifications.html', notifications=notifications)

@app.context_processor
def inject_unread_notifications():
    if current_user.is_authenticated and current_user.role == 'patient':
        unread_count = Notification.query.filter_by(patient_id=current_user.id, read=False).count()
        return {'unread_notifications': unread_count}
    return {'unread_notifications': 0}

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateProfileForm()
    if form.validate_on_submit():
        try:
            if form.avatar.data:
                file = form.avatar.data
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                if not os.path.exists(app.config['UPLOAD_FOLDER']):
                    os.makedirs(app.config['UPLOAD_FOLDER'])
                file.save(file_path)
                current_user.avatar = filename
            
            current_user.full_name = form.full_name.data
            current_user.phone = form.phone.data
            current_user.email = form.email.data
            db.session.commit()
            flash('Your profile has been updated successfully!', 'success')
            return redirect(url_for('profile'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating your profile. Please try again.', 'danger') 
    
    elif request.method == 'GET':
        form.full_name.data = current_user.full_name
        form.phone.data = current_user.phone
        form.email.data = current_user.email
    
    return render_template('profile.html', form=form)

@app.route('/search_patient')
@login_required
def search_patient():
    if current_user.role != 'doctor':
        flash('Access denied. Doctors only.', 'danger')
        return redirect(url_for('index'))
    
    patients = User.query.filter_by(role='patient').all()
    return render_template('search_patient.html', patients=patients)

@app.route('/admin/users')
@login_required
def admin_users():
    if current_user.role != 'admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('index'))
    
    users = User.query.all()
    role_form = AdminUserManagementForm()
    password_form = AdminPasswordResetForm()
    return render_template('admin_users.html', users=users, role_form=role_form, password_form=password_form)

@app.route('/admin/update_role/<int:user_id>', methods=['POST'])
@login_required
def admin_update_role(user_id):
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
            return redirect(url_for('admin_users'))
        
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
    
    return redirect(url_for('admin_users'))

@app.route('/admin/reset_password/<int:user_id>', methods=['POST'])
@login_required
def admin_reset_password(user_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin only.', 'danger')
        return redirect(url_for('index'))
    
    if not request.form.get('csrf_token'):
        flash('Invalid CSRF token. Please try again.', 'danger')
        return redirect(url_for('admin_users'))

    user = User.query.get_or_404(user_id)
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not new_password or not confirm_password:
        flash('Both password fields are required.', 'danger')
        return redirect(url_for('admin_users'))

    if new_password != confirm_password:
        flash('Passwords do not match.', 'danger')
        return redirect(url_for('admin_users'))

    try:
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        flash(f'Password for user {user.username} has been reset successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while resetting the password. Please try again.', 'danger')
        print(str(e))  # For debugging

    return redirect(url_for('admin_users'))

if not os.path.exists('static/uploads'):
    os.makedirs('static/uploads')

with app.app_context():
    db.create_all()
    # Create admin user if not exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin',
                     email='admin@example.com',
                     password_hash=generate_password_hash('admin'),
                     role='admin')
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)