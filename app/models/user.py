from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    phone = db.Column(db.String(20))
    full_name = db.Column(db.String(100))
    avatar = db.Column(db.String(200))
    role = db.Column(db.String(20))
    records = db.relationship('MedicalRecord', backref='patient', lazy=True)
    notifications = db.relationship('Notification', backref='patient', lazy=True)
    reset_code = db.Column(db.String(6))
    reset_code_expiry = db.Column(db.DateTime)