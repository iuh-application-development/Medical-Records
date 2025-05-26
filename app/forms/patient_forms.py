from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, DateField, SubmitField, FloatField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional

class UpdateProfileForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    phone = StringField('Phone', validators=[DataRequired(), Length(min=10, max=15)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    avatar = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

class MedicalRecordForm(FlaskForm):
    date = DateField('Date', validators=[DataRequired()], format='%Y-%m-%d')
    hgb = FloatField('HGB (g/dL)', validators=[Optional(), NumberRange(min=0, max=100, message='HGB must be between 0 and 100')])
    rbc = FloatField('RBC (M/μL)', validators=[Optional(), NumberRange(min=0, max=100, message='RBC must be between 0 and 100')])
    wbc = FloatField('WBC (K/μL)', validators=[Optional(), NumberRange(min=0, max=100, message='WBC must be between 0 and 100')])
    plt = FloatField('PLT (K/μL)', validators=[Optional(), NumberRange(min=0, max=1000, message='PLT must be between 0 and 1000')])
    hct = FloatField('HCT (%)', validators=[Optional(), NumberRange(min=0, max=100, message='HCT must be between 0 and 100')])
    glucose = FloatField('Glucose (mg/dL)', validators=[Optional(), NumberRange(min=0, max=1000, message='Glucose must be between 0 and 1000')])
    creatinine = FloatField('Creatinine (mg/dL)', validators=[Optional(), NumberRange(min=0, max=100, message='Creatinine must be between 0 and 100')])
    alt = FloatField('ALT (U/L)', validators=[Optional(), NumberRange(min=0, max=1000, message='ALT must be between 0 and 1000')])
    cholesterol = FloatField('Cholesterol (mg/dL)', validators=[Optional(), NumberRange(min=0, max=1000, message='Cholesterol must be between 0 and 1000')])
    crp = FloatField('CRP (mg/L)', validators=[Optional(), NumberRange(min=0, max=100, message='CRP must be between 0 and 100')])
    submit = SubmitField('Save Record')