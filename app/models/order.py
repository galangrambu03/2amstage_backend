from app import db
from datetime import datetime

class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    total_harga = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    status_pembayaran = db.Column(
        db.Enum("pending", "paid", "cancelled", "expired", name="order_status"),
        nullable=False,
        default="pending"
    )
    waktu_order = db.Column(db.DateTime, default=datetime.now)
    expired_at = db.Column(db.DateTime, nullable=True)
    paid_at = db.Column(db.DateTime, nullable=True)

    order_details = db.relationship(
        "OrderDetail", backref="order", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "event_id": self.event_id,
            "total_harga": float(self.total_harga),
            "status_pembayaran": self.status_pembayaran,
            "waktu_order": self.waktu_order.isoformat() if self.waktu_order else None,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
        }