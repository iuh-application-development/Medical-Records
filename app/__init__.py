from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_wtf.csrf import CSRFProtect
from itsdangerous import URLSafeTimedSerializer
from app.config import Config
import os

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
csrf = CSRFProtect()
s = None

def create_app():
    app = Flask(__name__, 
                template_folder='../templates',  # Chỉ định đường dẫn đến thư mục templates
                static_folder='../static')       # Chỉ định đường dẫn đến thư mục static
    
    # Load configuration from Config class
    app.config.from_object(Config)

    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize extensions with app
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    mail.init_app(app)

    # Initialize URL safe serializer
    global s
    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    
    # Ensure upload directory exists
    upload_dir = os.path.join(app.root_path, '..', app.config['UPLOAD_FOLDER'])
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    @app.route('/')
    def index():
        return render_template('index.html')

    # Import and register blueprints
    from app.routes import admin, patient, doctor, auth
    from app.routes.chat_ai import bp as chat_ai_bp
    app.register_blueprint(admin.bp, url_prefix='/admin')
    app.register_blueprint(patient.bp, url_prefix='/patient')
    app.register_blueprint(doctor.bp, url_prefix='/doctor')
    app.register_blueprint(auth.bp)
    app.register_blueprint(chat_ai_bp, url_prefix='/chat-ai')

    # Setup user loader
    from app.models.user import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Import và tạo các bảng trong database
    with app.app_context():
        from app.models.user import User
        from app.models.medical_record import MedicalRecord, Notification
        from app.models.chat_history import ChatHistory
        db.create_all()
        print("Database tables created")
    
    return app