from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from flask_mail import Message
from app.models.user import User
from app.forms import (LoginForm, RegistrationForm, ResetPasswordForm, 
                    ResetPasswordRequestForm)
# Thay đổi dòng import
from app import db, s, mail

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
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

@bp.route('/register', methods=['GET', 'POST'])
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
        return redirect(url_for('auth.login'))
    return render_template('register.html', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = s.dumps(user.email, salt='reset-password-salt')
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            msg = Message('Password Reset Request',
                        sender='noreply@yourdomain.com',
                        recipients=[user.email])
            msg.body = f'''To reset your password, visit the following link:
{reset_url}

If you did not make this request, simply ignore this email.
'''
            mail.send(msg)
            flash('Check your email for instructions to reset your password.', 'info')
            return redirect(url_for('auth.login'))
        flash('Email address not found.', 'error')
    return render_template('reset_password_request.html', form=form)

@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    try:
        email = s.loads(token, salt='reset-password-salt', max_age=3600)  # Token expires in 1 hour
    except:
        flash('The password reset link is invalid or has expired.', 'error')
        return redirect(url_for('auth.reset_password_request'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=email).first()
        if user:
            user.password_hash = generate_password_hash(form.password.data)
            db.session.commit()
            flash('Your password has been reset.', 'success')
            return redirect(url_for('auth.login'))
    return render_template('reset_password.html', form=form)

@bp.route('/send_reset_code', methods=['POST'])
def send_reset_code():
    email = request.json.get('email')
    if not email:
        return jsonify({'error': 'Email is required'}), 400
        
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'No account found with this email'}), 404
    
    # Generate a 6-digit code
    reset_code = ''.join(random.choices('0123456789', k=6))
    
    # Store the code and expiration time (10 minutes from now)
    user.reset_code = reset_code
    user.reset_code_expiry = datetime.utcnow() + timedelta(minutes=10)
    db.session.commit()
    
    # Send email with reset code
    try:
        msg = Message('Password Reset Code',
                     sender='noreply@yourdomain.com',
                     recipients=[email])
        msg.body = f'''Your password reset code is: {reset_code}
        
This code will expire in 10 minutes.
If you did not request a password reset, please ignore this email.'''
        mail.send(msg)
        return jsonify({'message': 'Reset code sent successfully'}), 200
    except Exception as e:
        return jsonify({'error': 'Failed to send reset code'}), 500

@bp.route('/verify_reset_code', methods=['POST'])
def verify_reset_code():
    email = request.json.get('email')
    code = request.json.get('code')
    
    if not email or not code:
        return jsonify({'error': 'Email and code are required'}), 400
        
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'Invalid email'}), 404
        
    if not user.reset_code or not user.reset_code_expiry:
        return jsonify({'error': 'No reset code requested'}), 400
        
    if datetime.utcnow() > user.reset_code_expiry:
        return jsonify({'error': 'Reset code has expired'}), 400
        
    if user.reset_code != code:
        return jsonify({'error': 'Invalid reset code'}), 400
        
    return jsonify({'message': 'Code verified successfully'}), 200

@bp.route('/reset_password_with_code', methods=['POST'])
def reset_password_with_code():
    email = request.json.get('email')
    code = request.json.get('code')
    new_password = request.json.get('new_password')
    
    if not email or not code or not new_password:
        return jsonify({'error': 'All fields are required'}), 400
        
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'Invalid email'}), 404
        
    if not user.reset_code or not user.reset_code_expiry:
        return jsonify({'error': 'No reset code requested'}), 400
        
    if datetime.utcnow() > user.reset_code_expiry:
        return jsonify({'error': 'Reset code has expired'}), 400
        
    if user.reset_code != code:
        return jsonify({'error': 'Invalid reset code'}), 400
    
    # Update password
    user.password_hash = generate_password_hash(new_password)
    # Clear reset code
    user.reset_code = None
    user.reset_code_expiry = None
    db.session.commit()
    
    return jsonify({'message': 'Password reset successfully'}), 200