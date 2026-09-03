from flask import Flask

# Creare and configure Flask application
def create_app():
    # Flask application object
    app = Flask(__name__)
    #Home route
    @app.route('/Home')
    def home():
        return "This is our Home page"

    #Returning flask application object
    return app