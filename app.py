from flask import Flask, render_template, request, redirect, url_for, flash, send_file, make_response, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from forms import RegistrationForm, LoginForm, UpdateProfileForm, MedicalRecordForm, NotificationForm, ResetPasswordRequestForm, ResetPasswordForm, AdminUserManagementForm, AdminPasswordResetForm
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import os
import pandas as pd
import plotly.express as px
import json
from itsdangerous import URLSafeTimedSerializer
from flask_wtf.csrf import CSRFProtect
import uuid
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///medical_records.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your-email-password'

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