from datetime import datetime, timezone

from app.extensions import db


class FlightSchedule(db.Model):
    __tablename__ = "flight_schedules"

    id = db.Column(db.Integer, primary_key=True)

    flight_id = db.Column(
        db.Integer,
        db.ForeignKey("flights.id"),
        nullable=False
    )

    departure_at = db.Column(db.DateTime(timezone=True), nullable=False)
    arrival_at = db.Column(db.DateTime(timezone=True), nullable=False)

    available_seats = db.Column(db.Integer, nullable=False)

    status = db.Column(
        db.String(30),
        nullable=False,
        default="SCHEDULED"
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    flight = db.relationship("Flight", back_populates="schedules")

    bookings = db.relationship("Booking", back_populates="schedule")
    ratings = db.relationship("PassengerRating", back_populates="schedule")

    __table_args__ = (
        db.CheckConstraint(
            "available_seats >= 0",
            name="check_available_seats"
        ),
    )

    def __repr__(self):
        return f"<FlightSchedule {self.id}>"
