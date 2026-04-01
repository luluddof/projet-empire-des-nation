from datetime import UTC, datetime

from ..extensions import db


class Utilisateur(db.Model):
    __tablename__ = "utilisateur"

    id = db.Column(db.String(20), primary_key=True)  # Discord snowflake ID
    username = db.Column(db.String(100), nullable=False)
    avatar = db.Column(db.String(100), nullable=True)
    is_mj = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), nullable=False)

    stocks = db.relationship(
        "Stock", backref="utilisateur", lazy=True, cascade="all, delete-orphan"
    )
    gains_passifs = db.relationship(
        "GainPassif", backref="utilisateur", lazy=True, cascade="all, delete-orphan"
    )
    transactions = db.relationship(
        "Transaction", backref="utilisateur", lazy=True, cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "avatar": self.avatar,
            "is_mj": self.is_mj,
            "created_at": self.created_at.isoformat(),
        }
