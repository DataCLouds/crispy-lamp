from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

#Creates shared object that can be imported across multiple files
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()