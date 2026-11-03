
from datetime import datetime, timezone

from app.extensions import db


class PaymentAttempt(db.Model):
    __tablename__ = "payment_attempts"

    id = db.Column(db.Integer, primary_key=True)

    payment_id = db.Column(
        db.Integer,
        db.ForeignKey("payments.id"),
        nullable=False
    )

    provider = db.Column(db.String(30), nullable=False)
    provider_reference = db.Column(db.String(100), unique=True)
    transaction_reference = db.Column(db.String(100), unique=True)

    status = db.Column(db.String(30), nullable=False, default="PENDING")

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    payment = db.relationship(
        "Payment",
        back_populates="attempts"
    )

    __table_args__ = (
        db.CheckConstraint(
            "provider IN ('DARAJA', 'FLUTTERWAVE')",
            name="check_payment_attempt_provider"
        ),
    )

    def __repr__(self):
        return f"<PaymentAttempt {self.id}: {self.status}>"

