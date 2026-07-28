from flask import Blueprint, request, jsonify
from app import db
from app.models.event import Event
from app.models.ticket_category import TicketCategory
from app.utils.decorators import role_required

tc_bp = Blueprint('ticket_categories', __name__, url_prefix='/api/events/<int:event_id>/categories')

@tc_bp.route('', methods=['GET'])
def get_categoris(event_id):
    event = Event.query.get(event_id)
    if not event :
        return jsonify({
            "message": "Event not found"
        }), 404
    
    categories = TicketCategory.query.filter_by(event_id=event_id).all()
    return jsonify([c.to_dict() for c in categories])

@tc_bp.route('', methods=["POST"])
@role_required('organizer', 'super_admin')
def create_category(event_id):
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"message" : "Event not foud"}), 404
    
    data = request.get_json()

    nama_kategori = data.get('nama_kategori')
    harga = data.get('harga')
    kuota = data.get('kuota')

    if not nama_kategori or harga is None or kuota is None:
        return jsonify({"message": 'nama_kategori, harga, and kuota must be filled.'})
    
    new_category = TicketCategory(
        event_id=event_id,
        nama_kategori=nama_kategori,
        harga=harga,
        kuota=kuota,
        sisa_kuota=kuota
    )

    db.session.add(new_category)
    db.session.commit()

    return jsonify({
        "message": "Ticket Categories Has Been Added!",
        "category": new_category.to_dict()
    }), 201


@tc_bp.route('/<int:category_id>', methods=['PUT'])
@role_required('organizer', 'super_admin')
def update_category(event_id, category_id):
    category = TicketCategory.query.filter_by(id=category_id, event_id=event_id).first()
    if not category:
        return jsonify({"message": "Category not found"}), 404
    
    data = request.get_json()

    for field in ['nama_kategori', 'harga', 'kuota']:
        if field in data:
            setattr(category, field, data[field])
    
    db.session.commit()

    return jsonify({
        "message": "Category ticket has been updated",
        "category": category.to_dict()
    }), 200

@tc_bp.route('/<int:category_id>', methods=["DELETE"])
@role_required('organizer', 'super_admin')
def delete_category(event_id, category_id):
    category = TicketCategory.query.filter_by(id=category_id, event_id=event_id).first()
    if not category:
        return jsonify({
            'message': "Category not found."
        }), 404
    db.session.delete(category)
    db.session.commit()

    return jsonify({'message': 'Kategory has been deleted'}), 200
