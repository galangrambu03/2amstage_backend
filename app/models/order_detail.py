from app import db

class OrderDetail(db.Model):
    __tablename__ = "order_details"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    ticket_category_id = db.Column(db.Integer, db.ForeignKey("ticket_categories.id"), nullable=False)
    jumlah = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False)

    tickets = db.relationship(
        "Ticket", backref="order_detail", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "ticket_category_id": self.ticket_category_id,
            "jumlah": self.jumlah,
            "subtotal": float(self.subtotal),
        }