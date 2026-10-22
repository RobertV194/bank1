"""Моделі бази даних (SQLAlchemy / SQLite)."""
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class OperationLog(db.Model):
    """Журнал операцій над чергами та стеком."""

    __tablename__ = "operation_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    structure = db.Column(db.String(50), nullable=False)
    operation_type = db.Column(db.String(50), nullable=False)
    value = db.Column(db.String(255), nullable=True)
    timestamp = db.Column(db.DateTime, nullable=False,
                          default=lambda: datetime.now(timezone.utc))
    description = db.Column(db.Text, nullable=True)

    def to_dict(self) -> dict:
        """Серіалізація запису у словник (для JSON / CSV)."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "structure": self.structure,
            "operation_type": self.operation_type,
            "value": self.value,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S") if self.timestamp else None,
            "description": self.description,
        }
