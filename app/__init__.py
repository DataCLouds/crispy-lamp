from flask import Flask
from .extensions import db, login_manager
from .config import Config
from .models import User 

# Create and configure Flask application
def create_app():
    app = Flask(__name__)

    # Load configuration from Config class
    app.config.from_object(Config)
    db.init_app(app)

    # Flask-Login setup
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"  # your route is auth.login
    login_manager.login_message = "Please log in."
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register blueprints
    from .main.routes import main_bp
    app.register_blueprint(main_bp)

    from .auth.routes import auth_bp
    app.register_blueprint(auth_bp)

    #Returning flask application object
    return app