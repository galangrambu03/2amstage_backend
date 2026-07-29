from flask import Blueprint, request, jsonify
from app import db
from app.models.ticket import Ticket
from app.utils.decorators import role_required
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

tickets_bp = Blueprint('tickets', __name__, url_prefix='/api/tickets')

@tickets_bp.route("/my", methods=["GET"])
@jwt_required()
def get_my_tickets():
    user_id = get_jwt_identity()

    from app.models.order_detail import OrderDetail
    from app.models.order import Order

    tickets = (
        db.session.query(Ticket)
        .join(OrderDetail, Ticket.order_detail_id == OrderDetail.id)
        .join(Order, OrderDetail.order_id == Order.id)
        .filter(Order.user_id == user_id)
        .all()
    )

    return jsonify([t.to_dict() for t in tickets]), 200

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
    
    if ticket.status == "used":
        return jsonify({
            "status": "already_used",
            "message": f"Ticket has been used for {ticket.used_at.isoformat() if ticket.used_at else '-'}"
        }), 400
    
    if ticket.status == "void":
        return jsonify({
            "status":"void",
            "message":"This ticket was expired (void)"
        }), 400
    
    ticket.status = 'used'
    ticket.used_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Tickes valid, check-in success!",
        "ticket": ticket.to_dict(include_qr=False)
    }), 200
