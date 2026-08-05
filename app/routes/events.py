from flask import Blueprint, request, jsonify
from app import db
from app.models.event import Event
from app.utils.decorators import role_required
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
from werkzeug.utils import secure_filename
from flask import current_app
from datetime import datetime

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

events_bp = Blueprint('events', __name__, url_prefix='/api/events')

@events_bp.route('', methods=['GET'])
def get_all_event():
    events = Event.query.filter_by(status='published').all()
    result = []
    for e in events:
        data = e.to_dict()
        total_kuota = sum(tc.kuota for tc in e.ticket_categories)
        total_sisa = sum(tc.sisa_kuota for tc in e.ticket_categories)
        terjual = total_kuota - total_sisa
        data['progress_percent'] = round((terjual / total_kuota) * 100) if total_kuota > 0 else 0
        harga_list = [tc.harga for tc in e.ticket_categories]
        data['harga_termurah'] = min(harga_list) if harga_list else None
        result.append(data)
    return jsonify(result), 200

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
    data = request.form  # ganti dari request.get_json()
    user_id = get_jwt_identity()

    required_fields = ['nama', 'tanggal', 'waktu', 'lokasi']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'message': f'{field} Must be filled'}), 400

    poster_url = None
    if 'poster' in request.files:
        file = request.files['poster']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(f"{user_id}_{int(datetime.now().timestamp())}_{file.filename}")
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            poster_url = f"/static/uploads/{filename}"

    new_event = Event(
        organizer_id=user_id,
        nama=data['nama'],
        deskripsi=data.get('deskripsi'),
        artis=data.get('artis'),
        tanggal=data['tanggal'],
        waktu=data['waktu'],
        lokasi=data['lokasi'],
        poster_url=poster_url,
        status=data.get('status', 'draft')
    )

    db.session.add(new_event)
    db.session.commit()

    return jsonify({
        "message": 'Event succesfully added!',
        "event": new_event.to_dict()
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

    data = request.form

    for field in ["nama", "deskripsi", "artis", "tanggal", "waktu", "lokasi", "status", "layout_type"]:
        if field in data:
            setattr(event, field, data[field])

    if "zone_mapping" in data:
        try:
            event.zone_mapping = json.loads(data["zone_mapping"])
        except (ValueError, TypeError):
            return jsonify({"message": "zone_mapping harus berupa JSON valid"}), 400

    if 'poster' in request.files:
        file = request.files['poster']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(f"{user_id}_{int(datetime.now().timestamp())}_{file.filename}")
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            event.poster_url = f"/static/uploads/{filename}"

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

    

