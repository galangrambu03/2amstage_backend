from app import db
from datetime import datetime

class ProfileBadge(db.Model):
    __tablename__ = "profile_badges"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    is_visible = db.Column(db.Boolean, nullable=False, default=True)
    display_order = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)

    __table_args__ = (
        db.UniqueConstraint("user_id", "event_id", name="uq_user_event_badge"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "event_id": self.event_id,
            "is_visible": self.is_visible,
            "display_order": self.display_order,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
