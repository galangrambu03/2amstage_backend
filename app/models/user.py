from app import db
from datetime import datetime
import bcrypt

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nama = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(
        db.Enum("super_admin", "organizer", "customer", "petugas", name="user_role"),
        nullable=False,
        default="customer"
    )
    no_hp = db.Column(db.String(20), nullable=True)
    username = db.Column(db.String(50), unique=True, nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, password):
        return bcrypt.checkpw(
            password.encode("utf-8"), self.password_hash.encode("utf-8")
        )

    def to_dict(self, include_email=True):
        from app.models.follow import Follow

        data = {
            "id": self.id,
            "nama": self.nama,
            "role": self.role,
            "username": self.username,
            "avatar_url": self.avatar_url,
            "bio": self.bio,
            "followers_count": Follow.query.filter_by(following_id=self.id).count(),
            "following_count": Follow.query.filter_by(follower_id=self.id).count(),
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
        if include_email:
            data["email"] = self.email
            data["no_hp"] = self.no_hp
        return data