from flask import Blueprint, jsonify
from app import db
from app.models.follow import Follow
from app.models.user import User
from flask_jwt_extended import jwt_required, get_jwt_identity

follows_bp = Blueprint("follows", __name__, url_prefix="/api/follows")


def _is_following(a_id, b_id):
    return Follow.query.filter_by(follower_id=a_id, following_id=b_id).first() is not None


@follows_bp.route("/<int:user_id>", methods=["POST"])
@jwt_required()
def follow_user(user_id):
    me = int(get_jwt_identity())
    if me == user_id:
        return jsonify({"message": "Kamu tidak bisa follow diri sendiri."}), 400

    target = User.query.get(user_id)
    if not target:
        return jsonify({"message": "User tidak ditemukan."}), 404

    if _is_following(me, user_id):
        return jsonify({"message": "Kamu sudah follow user ini."}), 409

    follow = Follow(follower_id=me, following_id=user_id)
    db.session.add(follow)
    db.session.commit()

    return jsonify({
        "message": f"Berhasil follow {target.nama}.",
        "is_mutual": _is_following(user_id, me),
    }), 201


@follows_bp.route("/<int:user_id>", methods=["DELETE"])
@jwt_required()
def unfollow_user(user_id):
    me = int(get_jwt_identity())
    follow = Follow.query.filter_by(follower_id=me, following_id=user_id).first()
    if not follow:
        return jsonify({"message": "Kamu belum follow user ini."}), 404

    db.session.delete(follow)
    db.session.commit()
    return jsonify({"message": "Berhasil unfollow."}), 200


@follows_bp.route("/status/<int:user_id>", methods=["GET"])
@jwt_required()
def follow_status(user_id):
    me = int(get_jwt_identity())
    following = _is_following(me, user_id)
    followed_by = _is_following(user_id, me)
    return jsonify({
        "is_following": following,
        "is_followed_by": followed_by,
        "is_mutual": following and followed_by,
    }), 200
