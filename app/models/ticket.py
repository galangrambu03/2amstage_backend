from app import db
from datetime import datetime

class Ticket(db.Model):
    __tablename__ = "tickets"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_detail_id = db.Column(db.Integer, db.ForeignKey("order_details.id"), nullable=False)
    ticket_code = db.Column(db.String(50), nullable=False, unique=True)
    qr_code_base64 = db.Column(db.Text, nullable=True)
    status = db.Column(
        db.Enum("unused", "used", "void", name="ticket_status"),
        nullable=False,
        default="unused"
    )
    used_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self, include_qr=True):
        data = {
            "id": self.id,
            "order_detail_id": self.order_detail_id,
            "ticket_code": self.ticket_code,
            "status": self.status,
            "used_at": self.used_at.isoformat() if self.used_at else None,
        }
        if include_qr:
            data["qr_code_base64"] = self.qr_code_base64
        return data