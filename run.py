from app import create_app

# Create flask application object
app = create_app()


if __name__ == "__main__":
    #Run the application
    app.run(debug=True)