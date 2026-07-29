from flask import Blueprint, jsonify
from app import db
from app.models.event import Event
from app.models.ticket_category import TicketCategory
from app.models.order import Order
from app.models.order_detail import OrderDetail
from app.models.ticket import Ticket
from app.utils.decorators import role_required
from flask_jwt_extended import get_jwt, get_jwt_identity

reports_bp = Blueprint("reports", __name__, url_prefix="/api/reports")


@reports_bp.route("/events/<int:event_id>", methods=["GET"])
@role_required("organizer", "super_admin")
def event_report(event_id):
    claims = get_jwt()
    user_id = get_jwt_identity()

    event = Event.query.get(event_id)
    if not event:
        return jsonify({"message": "Event tidak ditemukan"}), 404

    if claims.get("role") == "organizer" and str(event.organizer_id) != str(user_id):
        return jsonify({"message": "Kamu tidak punya akses ke event ini"}), 403

    paid_orders = Order.query.filter_by(event_id=event_id, status_pembayaran="paid").all()
    total_pendapatan = sum(float(o.total_harga) for o in paid_orders)
    total_order_paid = len(paid_orders)

    categories = TicketCategory.query.filter_by(event_id=event_id).all()
    category_stats = []
    total_tiket_terjual = 0
    total_checkin = 0

    for cat in categories:
        terjual = cat.kuota - cat.sisa_kuota

        checkin_count = (
            db.session.query(Ticket)
            .join(OrderDetail, Ticket.order_detail_id == OrderDetail.id)
            .filter(OrderDetail.ticket_category_id == cat.id, Ticket.status == "used")
            .count()
        )

        total_tiket_terjual += terjual
        total_checkin += checkin_count

        category_stats.append({
            "kategori": cat.nama_kategori,
            "harga": float(cat.harga),
            "kuota": cat.kuota,
            "terjual": terjual,
            "sisa_kuota": cat.sisa_kuota,
            "sudah_checkin": checkin_count
        })

    return jsonify({
        "event": {
            "id": event.id,
            "nama": event.nama,
            "tanggal": event.tanggal.isoformat() if event.tanggal else None,
            "status": event.status
        },
        "ringkasan": {
            "total_pendapatan": total_pendapatan,
            "total_order_paid": total_order_paid,
            "total_tiket_terjual": total_tiket_terjual,
            "total_checkin": total_checkin,
            "belum_checkin": total_tiket_terjual - total_checkin
        },
        "per_kategori": category_stats
    }), 200