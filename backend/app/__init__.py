
import os

from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from app.config import Config
from app.extensions import db, migrate, jwt, bcrypt
from app import models

from app.routes.health import health_bp
from app.routes.flights import flights_bp
from app.routes.schedules import schedules_bp
from app.routes.auth import auth_bp
from app.routes.bookings import bookings_bp
from app.routes.payments import payments_bp
from app.routes.ratings import ratings_bp


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
    app.register_blueprint(flights_bp)
    app.register_blueprint(schedules_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(bookings_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(ratings_bp)

    return app
