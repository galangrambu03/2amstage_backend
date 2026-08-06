from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models.user import User
from app.models.follow import Follow
from app.models.profile_badge import ProfileBadge
from app.models.event import Event
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
import uuid

profile_bp = Blueprint("profile", __name__, url_prefix="/api/profile")

ALLOWED_EXT = {"png", "jpg", "jpeg", "webp"}


def _allowed(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


@profile_bp.route("/me", methods=["GET"])
@jwt_required()
def get_my_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    return jsonify({"user": user.to_dict(include_email=True)}), 200


@profile_bp.route("/me", methods=["PUT"])
@jwt_required()
def update_my_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    username = request.form.get("username")
    bio = request.form.get("bio")
    nama = request.form.get("nama")

    if username is not None:
        username = username.strip().lower()
        if username and username != (user.username or ""):
            exists = User.query.filter(User.username == username, User.id != user.id).first()
            if exists:
                return jsonify({"message": "Username sudah dipakai, coba yang lain."}), 409
            user.username = username

    if bio is not None:
        user.bio = bio.strip()
    if nama:
        user.nama = nama.strip()

    file = request.files.get("avatar")
    if file and file.filename:
        if not _allowed(file.filename):
            return jsonify({"message": "Format foto tidak didukung (pakai png/jpg/jpeg/webp)."}), 400
        filename = f"avatar_{user.id}_{uuid.uuid4().hex[:8]}_{secure_filename(file.filename)}"
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        user.avatar_url = f"/static/uploads/{filename}"

    db.session.commit()
    return jsonify({"message": "Profil berhasil diperbarui.", "user": user.to_dict(include_email=True)}), 200


@profile_bp.route("/search", methods=["GET"])
@jwt_required()
def search_users():
    q = (request.args.get("q") or "").strip()
    me = int(get_jwt_identity())

    if not q:
        return jsonify({"users": []}), 200

    like = f"%{q}%"
    users = (
        User.query.filter(
            User.id != me,
            User.username.isnot(None),
            db.or_(User.username.ilike(like), User.nama.ilike(like)),
        )
        .order_by(User.username.asc())
        .limit(20)
        .all()
    )

    my_following_ids = {f.following_id for f in Follow.query.filter_by(follower_id=me).all()}

    result = [
        {**u.to_dict(include_email=False), "is_following": u.id in my_following_ids}
        for u in users
    ]

    return jsonify({"users": result}), 200


@profile_bp.route("/<username>", methods=["GET"])
def get_public_profile(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify({"message": "User tidak ditemukan."}), 404

    follower_count = Follow.query.filter_by(following_id=user.id).count()
    following_count = Follow.query.filter_by(follower_id=user.id).count()

    badges = (
        ProfileBadge.query.filter_by(user_id=user.id, is_visible=True)
        .order_by(ProfileBadge.display_order.asc())
        .all()
    )
    badge_data = []
    for b in badges:
        event = Event.query.get(b.event_id)
        if event:
            badge_data.append({
                "event_id": event.id,
                "nama_event": event.nama,
                "artis": event.artis,
                "tanggal": event.tanggal.isoformat() if event.tanggal else None,
                "poster_url": event.poster_url,
                "display_order": b.display_order,
            })

    return jsonify({
        "user": user.to_dict(include_email=False),
        "follower_count": follower_count,
        "following_count": following_count,
        "badges": badge_data,
    }), 200
