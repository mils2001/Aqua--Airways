from decimal import Decimal
 
import pytest
from flask_jwt_extended import create_access_token
 
from app import create_app
from app.extensions import db
from app.models import Booking, FlightSchedule, User
 
 
@pytest.fixture()
def password():
    return "TestPass123!"
 
 
@pytest.fixture()
def app():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "JWT_SECRET_KEY": "test-secret-key-at-least-32-characters-long",
        }
    )
 
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
 
 
@pytest.fixture()
def client(app):
    return app.test_client()
 
@pytest.fixture()
def make_user(app, password):
    """Factory: make_user(email=..., role=..., is_active=...)"""
 
    def _make(email="user@example.com", role="passenger",
              is_active=True, full_name="Test User"):
        user = User(full_name=full_name, email=email,
                    role=role, is_active=is_active)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user
 
    return _make
 
 
@pytest.fixture()
def admin(make_user):
    return make_user(email="admin@example.com", role="admin",
        full_name="Admin User")
 
 
@pytest.fixture()
def passenger(make_user):
    return make_user(email="passenger@example.com", role="passenger",
        full_name="Passenger One")
 
 
@pytest.fixture()
def other_passenger(make_user):
    return make_user(email="other@example.com", role="passenger",
        full_name="Passenger Two")
 
def _headers_for(user):
    token = create_access_token(identity=str(user.id))
    return {"Authorization": f"Bearer {token}"}
 
 
@pytest.fixture()
def admin_headers(admin):
    return _headers_for(admin)
 
 
@pytest.fixture()
def passenger_headers(passenger):
    return _headers_for(passenger)
 
 
@pytest.fixture()
def other_headers(other_passenger):
    return _headers_for(other_passenger)
 
 
@pytest.fixture()
def schedule(app):
    s = FlightSchedule()
    db.session.add(s)
    db.session.commit()
    return s
 
 
@pytest.fixture()
def make_booking(app, schedule):
    """Factory: make_booking(user, seats=1, amount=100, status="CONFIRMED")"""
 
    def _make(user, seats=1, amount=100, status="CONFIRMED"):
        booking = Booking(
            user_id=user.id,
            schedule_id=schedule.id,
            seats_booked=seats,
            total_amount=Decimal(str(amount)),
            status=status,
        )
        db.session.add(booking)
        db.session.commit()
        return booking
 
    return _make