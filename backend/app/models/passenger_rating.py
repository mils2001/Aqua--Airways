from datetime import datetime, timezone

from app.extensions import db


class PassengerRating(db.Model):
    __tablename__ = "passenger_ratings"

    id = db.Column(db.Integer, primary_key=True)

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

    rating = db.Column(db.Float, nullable=False)
    comment = db.Column(db.Text)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    user = db.relationship(
        "User",
        back_populates="ratings"
    )

    schedule = db.relationship(
        "FlightSchedule",
        back_populates="ratings"
    )

    __table_args__ = (
        db.CheckConstraint(
            "rating >= 1 AND rating <= 5",
            name="check_rating_range"
        ),
        db.UniqueConstraint(
            "user_id",
            "schedule_id",
            name="unique_user_schedule_rating"
        ),
    )

    def __repr__(self):
        return f"<PassengerRating {self.rating}>"
