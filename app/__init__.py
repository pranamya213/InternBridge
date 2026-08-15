from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
# login_manager.login_view = 'auth.login' # Uncomment when auth is implemented

@login_manager.user_loader
def load_user(user_id):
    """Dummy user loader to prevent Flask-Login exception during foundation phase."""
    return None

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
    
    from app.routes.errors import errors_bp
    app.register_blueprint(errors_bp)
    
    # Ensure instance folder exists
    import os
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
        
    return app
