from app import create_app,db

# Create flask application object
app = create_app()

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    # Run the application
    app.run(debug=True)
