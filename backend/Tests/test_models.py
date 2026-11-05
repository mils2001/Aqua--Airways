import pytest
from sqlalchemy.exc import IntegrityError
 
from app.extensions import db
 
 
def test_password_is_hashed_and_checkable(make_user, password):
    user = make_user()
    assert user.password_hash != password      
    assert user.check_password(password) is True
    assert user.check_password("wrong-password") is False
 
 
def test_user_defaults(make_user):
    user = make_user()
    assert user.role == "passenger"
    assert user.is_active is True
    assert user.created_at is not None
 
 
def test_email_must_be_unique(make_user):
    make_user(email="dup@example.com")
    with pytest.raises(IntegrityError):
        make_user(email="dup@example.com")
    db.session.rollback()
 
 
def test_booking_reference_is_generated(passenger, make_booking):
    booking = make_booking(passenger)
    assert booking.booking_reference
    assert len(booking.booking_reference) == 12
    assert booking.booking_reference == booking.booking_reference.upper()
 
 
def test_booking_references_are_unique(passenger, make_booking):
    first = make_booking(passenger)
    second = make_booking(passenger)
    assert first.booking_reference != second.booking_reference
 
 
def test_booking_default_status_is_pending(passenger, schedule):
    from decimal import Decimal
    from app.models import Booking
 
    booking = Booking(user_id=passenger.id, schedule_id=schedule.id,
                      seats_booked=1, total_amount=Decimal("50.00"))
    db.session.add(booking)
    db.session.commit()
    assert booking.status == "PENDING"
 
 
def test_booking_needs_at_least_one_seat(passenger, make_booking):
    with pytest.raises(IntegrityError):
        make_booking(passenger, seats=0)
    db.session.rollback()
 
 
def test_booking_amount_cannot_be_negative(passenger, make_booking):
    with pytest.raises(IntegrityError):
        make_booking(passenger, amount=-10)
    db.session.rollback()
 
 
def test_booking_links_back_to_user(passenger, make_booking):
    booking = make_booking(passenger)
    assert booking.user.email == passenger.email