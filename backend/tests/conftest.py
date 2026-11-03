
import pytest

from app import create_app
from app.extensions import db


class TestConfig:
    TESTING = True
    SECRET_KEY = "test-secret-key"
    JWT_SECRET_KEY = "test-jwt-secret-key-for-aqua-airways-2026"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_ACCESS_TOKEN_EXPIRES = 3600


@pytest.fixture()
def app():
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def registered_user(client):
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Test Passenger",
            "email": "passenger@example.com",
            "password": "TestPassword123"
        }
    )

    assert response.status_code == 201

    return response.get_json()["user"]


@pytest.fixture()
def auth_token(client, registered_user):
    response = client.post(
        "/api/auth/login",
        json={
            "email": "passenger@example.com",
            "password": "TestPassword123"
        }
    )

    assert response.status_code == 200

    return response.get_json()["access_token"]

