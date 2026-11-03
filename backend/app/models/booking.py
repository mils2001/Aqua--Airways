from datetime import datetime, timezone
import uuid

from app.extensions import db


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)

    booking_reference = db.Column(
        db.String(20),
        unique=True,
        nullable=False,
        default=lambda: uuid.uuid4().hex[:20].upper()
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    schedule_id = db.Column(
        db.Integer,
        db.ForeignKey("flight_schedules.id"),
        nullable=False
    )

    seats_booked = db.Column(db.Integer, nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)

    status = db.Column(
        db.String(30),
        nullable=False,
        default="PENDING"
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    user = db.relationship("User", back_populates="bookings")
    schedule = db.relationship("FlightSchedule", back_populates="bookings")
    seat_allocations = db.relationship(
        "BookingSeat",
        back_populates="booking",
        cascade="all, delete-orphan",
        order_by="BookingSeat.seat_number"
    )

    payment = db.relationship(
        "Payment",
        back_populates="booking",
        uselist=False,
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        db.CheckConstraint("seats_booked > 0", name="check_booked_seats"),
        db.CheckConstraint("total_amount >= 0", name="check_booking_amount"),
    )

    def __repr__(self):
        return f"<Booking {self.booking_reference}>"


class BookingSeat(db.Model):
    __tablename__ = "booking_seats"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(
        db.Integer,
        db.ForeignKey("bookings.id"),
        nullable=False
    )
    schedule_id = db.Column(
        db.Integer,
        db.ForeignKey("flight_schedules.id"),
        nullable=False
    )
    seat_number = db.Column(db.Integer, nullable=False)

    booking = db.relationship("Booking", back_populates="seat_allocations")

    __table_args__ = (
        db.UniqueConstraint(
            "schedule_id",
            "seat_number",
            name="unique_schedule_seat"
        ),
        db.UniqueConstraint(
            "booking_id",
            "seat_number",
            name="unique_booking_seat"
        ),
        db.CheckConstraint("seat_number > 0", name="check_seat_number"),
    )
