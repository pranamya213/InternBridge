from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User
    return User.query.get(int(user_id))

def create_app(config_name='default'):
    """Application factory pattern."""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    
    # Register blueprints
    from app.routes.main import main_bp
    app.register_blueprint(main_bp)
    
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/')

    from app.routes.student import student_bp
    app.register_blueprint(student_bp, url_prefix='/student')

    from app.routes.company import company_bp
    app.register_blueprint(company_bp, url_prefix='/company')

    from app.routes.admin import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    from app.routes.errors import errors_bp
    app.register_blueprint(errors_bp)
    
    # Ensure instance folder exists
    import os
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
        
    # Create database tables
    with app.app_context():
        from app import models  # Ensure models are imported
        db.create_all()

    return app
