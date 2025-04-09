from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SelectField, FloatField, DateField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[DataRequired(), Length(min=10, max=15)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')
    
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')
    
class UpdateProfileForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    phone = StringField('Phone', validators=[DataRequired(), Length(min=10, max=15)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    avatar = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

class NotificationForm(FlaskForm):
    message = StringField('Message', validators=[DataRequired(), Length(max=500)])
    submit = SubmitField('Send Notification')

class MedicalRecordForm(FlaskForm):
    date = DateField('Date', validators=[DataRequired()], format='%Y-%m-%d')
    hgb = StringField('HGB', validators=[DataRequired()])
    rbc = StringField('RBC', validators=[DataRequired()])
    wbc = StringField('WBC', validators=[DataRequired()])
    plt = StringField('PLT', validators=[DataRequired()])
    hct = StringField('HCT', validators=[DataRequired()])
    glucose = StringField('Glucose', validators=[DataRequired()])
    creatinine = StringField('Creatinine', validators=[DataRequired()])
    alt = StringField('ALT', validators=[DataRequired()])
    cholesterol = StringField('Cholesterol', validators=[DataRequired()])
    crp = StringField('CRP', validators=[DataRequired()])
    submit = SubmitField('Save Record')
    
class AdminUserManagementForm(FlaskForm):
    role = SelectField('Role', choices=[('patient', 'Patient'), ('doctor', 'Doctor'), ('admin', 'Admin')])
    current_role = StringField('Current Role')
    submit = SubmitField('Update Role')

class AdminPasswordResetForm(FlaskForm):
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Reset Password')