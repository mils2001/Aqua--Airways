
import os

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from app.config import Config
from app.extensions import db, migrate, jwt, bcrypt
from app.routes.health import health_bp


def create_app(config_class=Config):
    load_dotenv()

    app = Flask(__name__, instance_relative_config=True)

    app.config.from_object(config_class)

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": ["http://localhost:5173"]
            }
        }
    )

    app.register_blueprint(health_bp)

    return app

