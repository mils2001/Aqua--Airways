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
        default=lambda: uuid.uuid4().hex[:12].upper()
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
