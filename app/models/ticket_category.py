from app import db

class TicketCategory(db.Model):
    __tablename__ = "ticket_categories"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    nama_kategori = db.Column(db.String(100), nullable=False)
    harga = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    kuota = db.Column(db.Integer, nullable=False)
    sisa_kuota = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=None)

    def to_dict(self):
        return {
            "id": self.id,
            "event_id": self.event_id,
            "nama_kategori": self.nama_kategori,
            "harga": float(self.harga),
            "kuota": self.kuota,
            "sisa_kuota": self.sisa_kuota
        }