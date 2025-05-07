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
    notifications = db.relationship('Notification', foreign_keys='Notification.patient_id', backref='patient', lazy=True)
    sent_notifications = db.relationship('Notification', foreign_keys='Notification.doctor_id', backref='doctor', lazy=True)
    reset_code = db.Column(db.String(6))
    reset_code_expiry = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def get_unread_notifications_count(self):
        return sum(1 for n in self.notifications if not n.read)