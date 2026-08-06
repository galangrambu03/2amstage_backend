from flask import Blueprint, request, jsonify
from app import db
from app.models.profile_badge import ProfileBadge
from app.models.event import Event
from flask_jwt_extended import jwt_required, get_jwt_identity

badges_bp = Blueprint("badges", __name__, url_prefix="/api/badges")


@badges_bp.route("/me", methods=["GET"])
@jwt_required()
def get_my_badges():
    user_id = get_jwt_identity()
    badges = (
        ProfileBadge.query.filter_by(user_id=user_id)
        .order_by(ProfileBadge.display_order.asc())
        .all()
    )
    result = []
    for b in badges:
        event = Event.query.get(b.event_id)
        result.append({
            **b.to_dict(),
            "nama_event": event.nama if event else None,
            "artis": event.artis if event else None,
            "tanggal": event.tanggal.isoformat() if event and event.tanggal else None,
            "poster_url": event.poster_url if event else None,
        })
    return jsonify(result), 200


@badges_bp.route("/reorder", methods=["PUT"])
@jwt_required()
def update_badges():
    """Body: { "badges": [{ "id": 1, "is_visible": true, "display_order": 0 }, ...] }"""
    user_id = get_jwt_identity()
    data = request.get_json()
    items = data.get("badges", [])

    for item in items:
        badge = ProfileBadge.query.filter_by(id=item.get("id"), user_id=user_id).first()
        if not badge:
            continue
        if "is_visible" in item:
            badge.is_visible = bool(item["is_visible"])
        if "display_order" in item:
            badge.display_order = int(item["display_order"])

    db.session.commit()
    return jsonify({"message": "Urutan & visibilitas badge berhasil disimpan."}), 200
