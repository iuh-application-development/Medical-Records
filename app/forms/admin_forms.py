from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, HiddenField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo

class AdminUserManagementForm(FlaskForm):
    current_role = HiddenField('Current Role')
    role = SelectField('Role', choices=[('patient', 'Patient'), ('doctor', 'Doctor'), ('admin', 'Admin')], validators=[DataRequired()])
    submit = SubmitField('Update Role')

class AdminPasswordResetForm(FlaskForm):
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters long')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match')
    ])
    submit = SubmitField('Reset Password')