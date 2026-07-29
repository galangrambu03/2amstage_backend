from flask import Blueprint, request, jsonify
from app import db
from app.models.event import Event
from app.utils.decorators import role_required
from flask_jwt_extended import jwt_required, get_jwt_identity

events_bp = Blueprint('events', __name__, url_prefix='/api/events')

@events_bp.route('', methods=['GET'])
def get_all_event():
    events = Event.query.filter_by(status='published').all()
    return jsonify([e.to_dict() for e in events]), 200

@events_bp.route('/<int:event_id>', methods=['GET'])
def get_event_detail(event_id):
    event = Event.query.get(event_id)
    if not event:
        return jsonify({"message" : 'Event not found'}), 404
    
    data = event.to_dict()
    data['ticket_categories'] = [tc.to_dict() for tc in event.ticket_categories]
    return jsonify(data), 200

@events_bp.route('', methods=['POST'])
@role_required('organizer', 'super_admin')
def create_event():
    data = request.get_json()
    user_id = get_jwt_identity()

    required_fields = ['nama', 'tanggal', 'waktu', 'lokasi']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'message' :f'{field} Must be filled'}), 400

    new_event = Event(
        organizer_id=user_id,
        nama=data['nama'],
        deskripsi=data.get('deskripsi'),
        artis=data.get('artis'),
        tanggal=data['tanggal'],
        waktu=data['waktu'],
        lokasi=data['lokasi'],
        poster_url=data.get('poster_url'),
        status=data.get('status', 'draft')
    )

    db.session.add(new_event)
    db.session.commit()

    return jsonify({
        "message" : 'Event succesfully added!',
        "event" : new_event.to_dict()
    }), 201

@events_bp.route("/<int:event_id>", methods=["PUT"])
@role_required("organizer", "super_admin")
def update_event(event_id):
    from flask_jwt_extended import get_jwt, get_jwt_identity

    event = Event.query.get(event_id)
    if not event:
        return jsonify({"message": "Event Not Found"}), 404

    claims = get_jwt()
    user_id = get_jwt_identity()

    if claims.get("role") == "organizer" and str(event.organizer_id) != str(user_id):
        return jsonify({"message": "You don't have access to this event."}), 403

    data = request.get_json()

    for field in ["nama", "deskripsi", "artis", "tanggal", "waktu", "lokasi", "poster_url", "status"]:
        if field in data:
            setattr(event, field, data[field])

    db.session.commit()

    return jsonify({
        "message": "Event Succesfully Updated",
        "event": event.to_dict()
    }), 200

@events_bp.route("/<int:event_id>", methods=["DELETE"])
@role_required("organizer", "super_admin")
def delete_event(event_id):
    from flask_jwt_extended import get_jwt, get_jwt_identity

    event = Event.query.get(event_id)
    if not event:
        return jsonify({"message": "Event Not Found"}), 404

    claims = get_jwt()
    user_id = get_jwt_identity()

    if claims.get("role") == "organizer" and str(event.organizer_id) != str(user_id):
        return jsonify({"message": "You dont have access to this event."}), 403

    db.session.delete(event)
    db.session.commit()

    return jsonify({"message": "Event Successfully deleted"}), 200

    

