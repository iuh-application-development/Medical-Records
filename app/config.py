import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'hkhsl-hehehe-bshsbdfbshsbdf')
   
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'medical_records.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = 'medicalrecords.sys@gmail.com'
    MAIL_PASSWORD = 'xcltvkvwnezryvdb'
    MAIL_DEFAULT_SENDER = 'medicalrecords.sys@gmail.com'
    MAIL_MAX_EMAILS = None
    MAIL_ASCII_ATTACHMENTS = False
    
    @staticmethod
    def init_app(app):
        pass

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False