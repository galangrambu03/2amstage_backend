from flask import Blueprint, request, jsonify
from app import db
from app.models.ticket import Ticket
from app.models.order_detail import OrderDetail
from app.models.order import Order
from app.models.event import Event
from app.models.ticket_category import TicketCategory
from app.models.user import User
from app.models.profile_badge import ProfileBadge
from app.utils.decorators import role_required
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

tickets_bp = Blueprint('tickets', __name__, url_prefix='/api/tickets')

@tickets_bp.route("/my", methods=["GET"])
@jwt_required()
def get_my_tickets():
    user_id = get_jwt_identity()

    tickets = (
        db.session.query(Ticket)
        .join(OrderDetail, Ticket.order_detail_id == OrderDetail.id)
        .join(Order, OrderDetail.order_id == Order.id)
        .filter(Order.user_id == user_id)
        .all()
    )

    return jsonify([t.to_dict() for t in tickets]), 200


def _ticket_context(ticket):
    """Info tambahan (event, kategori, pembeli) buat ditampilkan ke petugas scan,
    di luar field mentah Ticket.to_dict()."""
    detail = OrderDetail.query.get(ticket.order_detail_id)
    if not detail:
        return {}
    order = Order.query.get(detail.order_id)
    event = Event.query.get(order.event_id) if order else None
    category = TicketCategory.query.get(detail.ticket_category_id)
    buyer = User.query.get(order.user_id) if order else None

    return {
        "event_nama": event.nama if event else None,
        "event_tanggal": event.tanggal.isoformat() if event and event.tanggal else None,
        "event_lokasi": event.lokasi if event else None,
        "kategori": category.nama_kategori if category else None,
        "pembeli": buyer.nama if buyer else None,
    }


def _ensure_badge(user_id, event_id):
    """Buat baris profile_badges otomatis kalau ini kali pertama user check-in
    tiket untuk event tersebut. display_order baru diletakkan paling akhir."""
    existing = ProfileBadge.query.filter_by(user_id=user_id, event_id=event_id).first()
    if existing:
        return
    max_order = db.session.query(db.func.max(ProfileBadge.display_order)).filter_by(user_id=user_id).scalar()
    next_order = (max_order + 1) if max_order is not None else 0
    db.session.add(ProfileBadge(user_id=user_id, event_id=event_id, display_order=next_order))


@tickets_bp.route('/validate', methods=['POST'])
@role_required('petugas', 'super_admin')
def validate_ticket():
    data = request.get_json()
    tickets_code = data.get("ticket_code")

    if not tickets_code:
        return jsonify({"status": "error", "message": "ticket_code must be filled"})

    ticket = (
        db.session.query(Ticket)
        .filter_by(ticket_code=tickets_code)
        .with_for_update()
        .first()
    )

    if not ticket:
        return jsonify({
            "status": 'Invalid',
            "message": "Ticket not found / invalid."
        }), 404

    context = _ticket_context(ticket)

    if ticket.status == "used":
        return jsonify({
            "status": "already_used",
            "message": f"Tiket sudah pernah digunakan pada {ticket.used_at.isoformat() if ticket.used_at else '-'}",
            "ticket": {**ticket.to_dict(include_qr=False), **context}
        }), 400

    if ticket.status == "void":
        return jsonify({
            "status": "void",
            "message": "Tiket ini sudah tidak berlaku (void)",
            "ticket": {**ticket.to_dict(include_qr=False), **context}
        }), 400

    if ticket.expires_at and datetime.now() > ticket.expires_at:   
        return jsonify({
            "status": "expired",
            "message": f"Tiket sudah kedaluwarsa sejak {ticket.expires_at.isoformat()}",
            "ticket": {**ticket.to_dict(include_qr=False), **context}
        }), 400

    ticket.status = "used"
    ticket.used_at = datetime.now()

    detail = OrderDetail.query.get(ticket.order_detail_id)
    order = Order.query.get(detail.order_id) if detail else None
    if order:
        _ensure_badge(order.user_id, order.event_id)

    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Ticket valid, check-in success!",
        "ticket": {**ticket.to_dict(include_qr=False), **context}
    }), 200
