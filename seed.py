print("it worked")

import os
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

from app import create_app
from app.extensions import db
from app.models import User, Booking, FlightSchedule
from app.models import Payment, PassengerRating
 

DEFAULT_PASSWORD = os.environ.get("SEED_PASSWORD", "ChangeMe123!")
FALLBACK_PRICE_PER_SEAT = Decimal("100.00")

USERS = [
    {"full_name": "Admin User", "email": "admin@kenya-airways.test", "role": "admin"},
    {"full_name": "Amina Wanjiru", "email": "amina@example.com", "role": "passenger"},
    {"full_name": "Brian Otieno", "email": "brian@example.com", "role": "passenger"},
    {"full_name": "Cynthia Mutua", "email": "cynthia@example.com", "role": "passenger"},
]

BOOKINGS = [
    ("amina@example.com", 0, 2, "CONFIRMED"),
    ("amina@example.com", 1, 1, "PENDING"),
    ("brian@example.com", 0, 3, "CONFIRMED"),
    ("brian@example.com", 2, 1, "CANCELLED"),
    ("cynthia@example.com", 1, 4, "CONFIRMED"),
    ("cynthia@example.com", 2, 2, "PENDING"),
]


def reset_data():
    for booking in Booking.query.all():
        db.session.delete(booking)
    db.session.commit()

    emails = [u["email"] for u in USERS]
    for user in User.query.filter(User.email.in_(emails)).all():
        db.session.delete(user)
    db.session.commit()
    print("Old sample data removed.")


def seed_users():
    users = {}
    for data in USERS:
        user = User.query.filter_by(email=data["email"]).first()
        if user:
            print(f"  user exists, skipped: {data['email']}")
        else:
            user = User(
                full_name=data["full_name"],
                email=data["email"],
                role=data["role"],
            )
            user.set_password(DEFAULT_PASSWORD)  # hashes the password
            db.session.add(user)
            print(f"  user created: {data['email']} ({data['role']})")
        users[data["email"]] = user
    db.session.commit()
    return users


def seed_bookings(users):
    if Booking.query.count() > 0:
        print("  bookings already exist, skipped (use --reset to start over)")
        return

    schedules = FlightSchedule.query.order_by(FlightSchedule.id).all()
    if not schedules:
        print("  no flight schedules found. Seed flights and schedules first.")
        return

    for email, schedule_pos, seats, status in BOOKINGS:
        schedule = schedules[schedule_pos % len(schedules)]
        price = getattr(schedule, "price", None) or FALLBACK_PRICE_PER_SEAT

        booking = Booking(
            user_id=users[email].id,
            schedule_id=schedule.id,
            seats_booked=seats,
            total_amount=Decimal(str(price)) * seats,
            status=status,
          
        )
        db.session.add(booking)
        print(f"  booking created: {email}, schedule {schedule.id}, "
            f"{seats} seat(s), {status}")
    db.session.commit()


def main():
    app = create_app()
    with app.app_context():
        if "--reset" in sys.argv:
            reset_data()

        print("Seeding users...")
        users = seed_users()

        print("Seeding bookings...")
        seed_bookings(users)

        print("Done.")


if __name__ == "__main__":
    main()