
from datetime import datetime, timezone

from app.extensions import db


class AquaRewardClaim(db.Model):
    __tablename__ = "aqua_reward_claims"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    points = db.Column(db.Integer, nullable=False, default=10)

    claim_date = db.Column(db.Date, nullable=False)

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    user = db.relationship("User", back_populates="reward_claims")

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "claim_date",
            name="unique_daily_aqua_claim"
        ),
        db.CheckConstraint(
            "points > 0",
            name="check_positive_aqua_points"
        ),
    )

    def __repr__(self):
        return f"<AquaRewardClaim user={self.user_id} points={self.points}>"

