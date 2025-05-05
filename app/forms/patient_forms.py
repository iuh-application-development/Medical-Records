from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, DateField, SubmitField
from wtforms.validators import DataRequired, Email, Length

class UpdateProfileForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    phone = StringField('Phone', validators=[DataRequired(), Length(min=10, max=15)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    avatar = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

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