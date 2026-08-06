from flask import Blueprint, request, jsonify
from app import db
from app.models.conversation import Conversation
from app.models.conversation_participant import ConversationParticipant
from app.models.message import Message
from app.models.follow import Follow
from app.models.user import User
from flask_jwt_extended import jwt_required, get_jwt_identity

chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")


def _is_following(a_id, b_id):
    return Follow.query.filter_by(follower_id=a_id, following_id=b_id).first() is not None


def _is_mutual(a_id, b_id):
    return _is_following(a_id, b_id) and _is_following(b_id, a_id)


def _is_participant(convo_id, user_id):
    return ConversationParticipant.query.filter_by(conversation_id=convo_id, user_id=user_id).first() is not None


def _find_existing_conversation(user_a, user_b):
    """Cari conversation 1-on-1 yang partisipannya persis 2 user ini."""
    convo_ids_a = {
        p.conversation_id for p in ConversationParticipant.query.filter_by(user_id=user_a).all()
    }
    for cid in convo_ids_a:
        participant_ids = {
            p.user_id for p in ConversationParticipant.query.filter_by(conversation_id=cid).all()
        }
        if participant_ids == {user_a, user_b}:
            return Conversation.query.get(cid)
    return None


@chat_bp.route("/conversations", methods=["POST"])
@jwt_required()
def start_conversation():
    me = int(get_jwt_identity())
    data = request.get_json()
    target_id = data.get("user_id")

    if not target_id:
        return jsonify({"message": "user_id wajib diisi."}), 400

    target_id = int(target_id)
    if target_id == me:
        return jsonify({"message": "Kamu tidak bisa chat dengan diri sendiri."}), 400

    target = User.query.get(target_id)
    if not target:
        return jsonify({"message": "User tidak ditemukan."}), 404

    if not _is_mutual(me, target_id):
        return jsonify({"message": "Kalian harus saling follow dulu untuk bisa chat."}), 403

    existing = _find_existing_conversation(me, target_id)
    if existing:
        return jsonify({"message": "Percakapan sudah ada.", "conversation": existing.to_dict()}), 200

    convo = Conversation()
    db.session.add(convo)
    db.session.flush()
    db.session.add(ConversationParticipant(conversation_id=convo.id, user_id=me))
    db.session.add(ConversationParticipant(conversation_id=convo.id, user_id=target_id))
    db.session.commit()

    return jsonify({"message": "Percakapan dimulai.", "conversation": convo.to_dict()}), 201


@chat_bp.route("/conversations", methods=["GET"])
@jwt_required()
def list_conversations():
    me = int(get_jwt_identity())
    my_participations = ConversationParticipant.query.filter_by(user_id=me).all()

    result = []
    for p in my_participations:
        convo = Conversation.query.get(p.conversation_id)
        others = ConversationParticipant.query.filter(
            ConversationParticipant.conversation_id == convo.id,
            ConversationParticipant.user_id != me,
        ).all()
        other_users = [User.query.get(o.user_id) for o in others]
        last_message = (
            Message.query.filter_by(conversation_id=convo.id)
            .order_by(Message.created_at.desc())
            .first()
        )
        result.append({
            "id": convo.id,
            "lawan_bicara": [u.to_dict(include_email=False) for u in other_users if u],
            "pesan_terakhir": last_message.to_dict() if last_message else None,
        })

    result.sort(
        key=lambda c: c["pesan_terakhir"]["created_at"] if c["pesan_terakhir"] else "",
        reverse=True,
    )
    return jsonify(result), 200


@chat_bp.route("/conversations/<int:convo_id>/messages", methods=["GET"])
@jwt_required()
def get_messages(convo_id):
    me = int(get_jwt_identity())
    if not _is_participant(convo_id, me):
        return jsonify({"message": "Kamu bukan bagian dari percakapan ini."}), 403

    messages = (
        Message.query.filter_by(conversation_id=convo_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    return jsonify([m.to_dict() for m in messages]), 200


@chat_bp.route("/conversations/<int:convo_id>/messages", methods=["POST"])
@jwt_required()
def send_message(convo_id):
    me = int(get_jwt_identity())
    if not _is_participant(convo_id, me):
        return jsonify({"message": "Kamu bukan bagian dari percakapan ini."}), 403

    data = request.get_json()
    isi = (data.get("isi") or "").strip()
    if not isi:
        return jsonify({"message": "Pesan tidak boleh kosong."}), 400

    # Kalau salah satu pihak sudah unfollow, riwayat lama tetap bisa dibaca
    # tapi TIDAK boleh kirim pesan baru selama belum mutual follow lagi.
    others = ConversationParticipant.query.filter(
        ConversationParticipant.conversation_id == convo_id,
        ConversationParticipant.user_id != me,
    ).all()
    for o in others:
        if not _is_mutual(me, o.user_id):
            return jsonify({
                "message": "Kalian sudah tidak saling follow, tidak bisa mengirim pesan baru."
            }), 403

    message = Message(conversation_id=convo_id, sender_id=me, isi=isi)
    db.session.add(message)
    db.session.commit()

    return jsonify({"message": "Pesan terkirim.", "data": message.to_dict()}), 201
