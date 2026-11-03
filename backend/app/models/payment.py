from datetime import datetime, timezone

from app.extensions import db


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)

    booking_id = db.Column(
        db.Integer,
        db.ForeignKey("bookings.id"),
        unique=True,
        nullable=False
    )

    amount = db.Column(db.Numeric(10, 2), nullable=False)

    currency = db.Column(
        db.String(10),
        nullable=False,
        default="KES"
    )

    payment_method = db.Column(db.String(50))

    transaction_reference = db.Column(
        db.String(100),
        unique=True
    )

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

    booking = db.relationship("Booking", back_populates="payment")

    __table_args__ = (
        db.CheckConstraint("amount >= 0", name="check_payment_amount"),
    )

    def __repr__(self):
        return f"<Payment {self.id}>"
