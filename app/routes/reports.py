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


@reports_bp.route("/dashboard", methods=["GET"])
@role_required("organizer", "super_admin")
def dashboard_summary():
    claims = get_jwt()
    user_id = get_jwt_identity()

    event_query = Event.query
    if claims.get("role") == "organizer":
        event_query = event_query.filter_by(organizer_id=user_id)
    events = event_query.all()
    event_ids = [e.id for e in events]

    if event_ids:
        paid_orders = Order.query.filter(
            Order.event_id.in_(event_ids), Order.status_pembayaran == "paid"
        ).all()
    else:
        paid_orders = []

    total_pendapatan = sum(float(o.total_harga) for o in paid_orders)
    total_order_paid = len(paid_orders)

    total_tiket_terjual = 0
    total_checkin = 0
    for e in events:
        for cat in e.ticket_categories:
            total_tiket_terjual += (cat.kuota - cat.sisa_kuota)
            total_checkin += (
                db.session.query(Ticket)
                .join(OrderDetail, Ticket.order_detail_id == OrderDetail.id)
                .filter(OrderDetail.ticket_category_id == cat.id, Ticket.status == "used")
                .count()
            )

    status_counts = {}
    for e in events:
        status_counts[e.status] = status_counts.get(e.status, 0) + 1

    upcoming = sorted(
        [e for e in events if e.status == "published"],
        key=lambda e: e.tanggal
    )[:5]

    return jsonify({
        "ringkasan": {
            "total_event": len(events),
            "total_pendapatan": total_pendapatan,
            "total_order_paid": total_order_paid,
            "total_tiket_terjual": total_tiket_terjual,
            "total_checkin": total_checkin,
        },
        "status_event": status_counts,
        "event_terdekat": [
            {
                "id": e.id,
                "nama": e.nama,
                "tanggal": e.tanggal.isoformat() if e.tanggal else None,
                "lokasi": e.lokasi,
                "poster_url": e.poster_url,
            } for e in upcoming
        ]
    }), 200


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