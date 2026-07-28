from app import db
from datetime import datetime

class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    organizer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    nama = db.Column(db.String(150), nullable=False)
    deskripsi = db.Column(db.Text, nullable=True)
    artis = db.Column(db.String(150), nullable=True)
    tanggal = db.Column(db.Date, nullable=False)
    waktu = db.Column(db.Time, nullable=False)
    lokasi = db.Column(db.String(200), nullable=False)
    poster_url = db.Column(db.String(255), nullable=True)
    status = db.Column(
        db.Enum("draft", "published", "sold_out", "selesai", "dibatalkan", name="event_status"),
        nullable=False,
        default="draft"
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    ticket_categories = db.relationship(
        "TicketCategory", backref="event", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "organizer_id": self.organizer_id,
            "nama": self.nama,
            "deskripsi": self.deskripsi,
            "artis": self.artis,
            "tanggal": self.tanggal.isoformat() if self.tanggal else None,
            "waktu": self.waktu.strftime("%H:%M:%S") if self.waktu else None,
            "lokasi": self.lokasi,
            "poster_url": self.poster_url,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }