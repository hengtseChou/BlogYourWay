from application import create_app
from application.config import ENV


app = create_app()

if __name__ == "__main__":
    # if ENV == "debug":
    #     app.run(debug=True)
    # else:
    #     app.run()
    app.run()