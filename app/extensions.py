from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

#Creates shared db object that can be imported across multiple files
db = SQLAlchemy()
login_manager = LoginManager()