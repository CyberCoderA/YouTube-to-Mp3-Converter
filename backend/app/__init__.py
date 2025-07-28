from flask import Flask
from flask_cors import CORS
from config import DevelopmentConfig

def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config.from_object(DevelopmentConfig)

    from .processes import main
    app.register_blueprint(main)

    return app