from application import create_app
from application.config import ENV


app = create_app()

if __name__ == "__main__":
    if ENV == "develop":
        app.run(debug=True)
    else:
        app.run()