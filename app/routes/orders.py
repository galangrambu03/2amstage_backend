from flask import Blueprint, request, jsonify
from app import db
from app.models.event import Event
from app.models.ticket_category import TicketCategory
from app.models.order import Order
from app.models.order_detail import OrderDetail
from app.models.ticket import Ticket
from app.utils.qr_generator import generate_qr_base64, generate_ticket_code
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from datetime import time as dtime

orders_bp = Blueprint('orders', __name__, url_prefix="/api/orders")

@orders_bp.route('', methods=["POST"])
@jwt_required()
def create_order():
    user_id = get_jwt_identity()
    data = request.get_json()

    event_id = data.get("event_id")
    items = data.get('items')

    if not event_id or not items or len(items) == 0:
        return jsonify({"message": "event_id and items must be filled!"}), 400

    event = Event.query.get(event_id)
    if not event:
        return jsonify({"message": "Event not found."}), 404
    
    total_harga = 0
    order_detail_data = []

    for item in items:
        category = TicketCategory.query.get(item.get('ticket_category_id'))
        jumlah = item.get("jumlah", 0)

        if not category or category.event_id != event_id:
            return jsonify({"message": "Ticket category doesnt valid fot this event."}), 400
        
        if jumlah <= 0:
            return jsonify({"message": "The sum of ticket must be more than 0"}), 400
        
        if category.sisa_kuota < jumlah:
            return jsonify({
                "message": f"Ticket Quota '{category.nama_kategori}' does not enough. Ticket left: {category.sisa_kuota} "
            }), 400
        
        subtotal = float(category.harga) * jumlah
        total_harga += subtotal

        order_detail_data.append({
            "category": category,
            "jumlah" : jumlah,
            "subtotal": subtotal
        })
    
    new_order = Order(
        user_id=user_id,
        event_id=event_id,
        total_harga=total_harga,
        status_pembayaran='pending',
        expired_at=datetime.now() + timedelta(minutes=10)
    )
    db.session.add(new_order)
    db.session.flush()

    for od in order_detail_data:
        new_detail = OrderDetail(
            order_id=new_order.id,
            ticket_category_id=od['category'].id,
            jumlah=od['jumlah'],
            subtotal=od['subtotal']
        )
        db.session.add(new_detail)
    
    db.session.commit()

    return jsonify({
        "message": "Order has been made, please proceed to payment.",
        "order": new_order.to_dict()
    }), 201

@orders_bp.route("/<int:order_id>/pay", methods=["POST"])
@jwt_required()
def pay_order(order_id):
    user_id = get_jwt_identity()
    order = Order.query.get(order_id)

    if not order:
        return jsonify({"message": "order not found."}), 404
    
    if str(order.user_id) != str(user_id):
        return jsonify({"message": "This order was not yours :("}), 403
    
    if order.status_pembayaran != "pending":
        return jsonify({"message": f"Order have done with status '{order.status_pembayaran}', can't be paid anymore." }), 400
    
    for detail in order.order_details:
        category = TicketCategory.query.get(detail.ticket_category_id)
        if category.sisa_kuota < detail.jumlah:
            return jsonify({
                "message": f"Ticket Quota '{category.nama_kategori}' does not enough."
            }), 400
    
    order.status_pembayaran='paid'
    order.paid_at = datetime.now()   

    generated_tickets = []

    event = Event.query.get(order.event_id)
    ticket_expiry = datetime.combine(event.tanggal, dtime(23, 59, 59)) + timedelta(days=1)

    for detail in order.order_details:
        category = TicketCategory.query.get(detail.ticket_category_id)
        category.sisa_kuota -= detail.jumlah

        for _ in range(detail.jumlah):
            ticket_code = generate_ticket_code()
            qr_base64 = generate_qr_base64(ticket_code)

            new_ticket = Ticket(
                order_detail_id=detail.id,
                ticket_code=ticket_code,
                qr_code_base64=qr_base64,
                status="unused",
                expires_at=ticket_expiry
            )
            db.session.add(new_ticket)
            generated_tickets.append(new_ticket)
        
    db.session.commit()

    return jsonify({
        "message": "payment success, ticket has been made!",
        "order": order.to_dict(),
        "tickets": [t.to_dict() for t in generated_tickets]
    }), 200

@orders_bp.route('/my', methods=["GET"])
@jwt_required()
def get_my_orders():
    user_id = get_jwt_identity()
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.waktu_order.desc()).all()
    return jsonify([o.to_dict() for o in orders]), 200


        
