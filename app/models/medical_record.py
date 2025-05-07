from app import db
from datetime import datetime

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
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    message = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)