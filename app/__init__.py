from flask import Flask
from .extensions import db
from .config import Config

# Creare and configure Flask application
def create_app():
    app = Flask(__name__)

    app.config.from_object(Config)

    db.init_app(app)

    from .auth.routes import auth_bp

    app.register_blueprint(auth_bp)

    @app.route('/Home')
    def home():
        return "This is our Home page"

    #Returning flask application object
    return app