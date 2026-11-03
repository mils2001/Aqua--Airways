from datetime import datetime, timezone

from app.extensions import db


class Flight(db.Model):
    __tablename__ = "flights"

    id = db.Column(db.Integer, primary_key=True)

    flight_number = db.Column(db.String(20), unique=True, nullable=False)
    origin = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)

    origin_code = db.Column(db.String(3), nullable=False)
    destination_code = db.Column(db.String(3), nullable=False)

    base_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_seats = db.Column(db.Integer, nullable=False)

    destination_image = db.Column(db.String(500))

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    schedules = db.relationship(
        "FlightSchedule",
        back_populates="flight",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        db.CheckConstraint("base_price >= 0", name="check_flight_price"),
        db.CheckConstraint("total_seats > 0", name="check_total_seats"),
    )

    def __repr__(self):
        return f"<Flight {self.flight_number}>"
