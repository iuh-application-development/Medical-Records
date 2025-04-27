from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from flask_mail import Message
from app.models.user import User
from app.forms import (LoginForm, RegistrationForm, ResetPasswordForm, 
                    ResetPasswordRequestForm)
from app import db, mail
import random
from flask import current_app

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
    try:
        data = request.get_json()
        print("Received data:", data)
        
        if not data:
            print("No JSON data received")
            return jsonify({'error': 'Không nhận được dữ liệu JSON'}), 400
            
        email = data.get('email')
        print("Email:", email)
        
        if not email:
            print("No email provided")
            return jsonify({'error': 'Vui lòng nhập địa chỉ email'}), 400
            
        user = User.query.filter_by(email=email).first()
        if not user:
            print(f"User not found for email: {email}")
            return jsonify({'error': 'Không tìm thấy tài khoản với email này'}), 404
        
        reset_code = ''.join(random.choices('0123456789', k=6))
        print(f"Generated reset code: {reset_code}")
        
        user.reset_code = reset_code
        user.reset_code_expiry = datetime.utcnow() + timedelta(minutes=1)
        
        try:
            db.session.commit()
            print("Reset code saved to database")
        except Exception as db_error:
            print(f"Database error: {str(db_error)}")
            db.session.rollback()
            return jsonify({'error': 'Lỗi cập nhật cơ sở dữ liệu'}), 500
        
        try:
            msg = Message(
                subject='CODE FOR RESET PASSWORD AT MEDICAL RECORD',
                recipients=[email],
                body=f'''Mã xác thực của bạn là: {reset_code}

Mã này sẽ hết hạn sau 1 phút.
Nếu bạn không yêu cầu đặt lại mật khẩu, vui lòng bỏ qua email này.'''
            )
            
            mail.send(msg)
            print("Email sent successfully")
            
            return jsonify({
                'message': 'Mã xác thực đã được gửi đến email của bạn',
                'expiresIn': 60
            }), 200
            
        except Exception as mail_error:
            print(f"Email error details: {str(mail_error)}")
            if hasattr(mail_error, 'stderr'):
                print(f"SMTP error output: {mail_error.stderr}")
            db.session.rollback()
            return jsonify({'error': f'Lỗi gửi email: {str(mail_error)}'}), 500
            
    except Exception as e:
        print(f"General error: {str(e)}")
        if hasattr(e, '__traceback__'):
            import traceback
            print("Traceback:")
            traceback.print_tb(e.__traceback__)
        db.session.rollback()
        return jsonify({'error': 'Có lỗi xảy ra. Vui lòng thử lại sau.'}), 500

@bp.route('/verify_reset_code', methods=['POST'])
def verify_reset_code():
    try:
        email = request.json.get('email')
        code = request.json.get('code')
        
        if not email or not code:
            return jsonify({'error': 'Vui lòng nhập đầy đủ thông tin'}), 400
            
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': 'Email không hợp lệ'}), 404
            
        if not user.reset_code or not user.reset_code_expiry:
            return jsonify({'error': 'Chưa có mã xác thực nào được gửi'}), 400
            
        if datetime.utcnow() > user.reset_code_expiry:
            return jsonify({'error': 'Mã xác thực đã hết hạn'}), 400
            
        if user.reset_code != code:
            return jsonify({'error': 'Mã xác thực không đúng'}), 400
            
        return jsonify({'message': 'Xác thực thành công'}), 200
        
    except Exception as e:
        print(f"Error verifying code: {str(e)}")
        return jsonify({'error': 'Có lỗi xảy ra. Vui lòng thử lại.'}), 500

@bp.route('/reset_password_with_code', methods=['POST'])
def reset_password_with_code():
    try:
        email = request.json.get('email')
        code = request.json.get('code')
        new_password = request.json.get('new_password')
        
        if not email or not code or not new_password:
            return jsonify({'error': 'Vui lòng nhập đầy đủ thông tin'}), 400
            
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': 'Email không hợp lệ'}), 404
            
        if not user.reset_code or not user.reset_code_expiry:
            return jsonify({'error': 'Chưa có mã xác thực nào được gửi'}), 400
            
        if datetime.utcnow() > user.reset_code_expiry:
            return jsonify({'error': 'Mã xác thực đã hết hạn'}), 400
            
        if user.reset_code != code:
            return jsonify({'error': 'Mã xác thực không đúng'}), 400
        
        user.password_hash = generate_password_hash(new_password)
        user.reset_code = None
        user.reset_code_expiry = None
        db.session.commit()
        
        return jsonify({'message': 'Đặt lại mật khẩu thành công'}), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error resetting password: {str(e)}")
        return jsonify({'error': 'Không thể đặt lại mật khẩu. Vui lòng thử lại sau.'}), 500