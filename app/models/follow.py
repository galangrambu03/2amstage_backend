from app import db
from datetime import datetime

class Follow(db.Model):
    __tablename__ = "follows"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    follower_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    following_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    __table_args__ = (
        db.UniqueConstraint("follower_id", "following_id", name="uq_follower_following"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "follower_id": self.follower_id,
            "following_id": self.following_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
