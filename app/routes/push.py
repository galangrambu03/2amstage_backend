import json
import os
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from pywebpush import webpush, WebPushException
from app import db
from app.models.push_subscription import PushSubscription

push_bp = Blueprint("push", __name__, url_prefix="/api/push")

VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY")
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY")
VAPID_CLAIMS_SUB = os.getenv("VAPID_CLAIMS_SUB", "mailto:admin@2amstage.com")


@push_bp.route("/vapid-public-key", methods=["GET"])
def get_vapid_public_key():
    return jsonify({"publicKey": VAPID_PUBLIC_KEY}), 200


@push_bp.route("/subscribe", methods=["POST"])
@jwt_required()
def subscribe():
    me = int(get_jwt_identity())
    data = request.get_json() or {}
    endpoint = data.get("endpoint")
    keys = data.get("keys") or {}
    p256dh = keys.get("p256dh")
    auth = keys.get("auth")

    if not endpoint or not p256dh or not auth:
        return jsonify({"message": "Data subscription tidak lengkap."}), 400

    existing = PushSubscription.query.filter_by(endpoint=endpoint).first()
    if existing:
        existing.user_id = me
        existing.p256dh = p256dh
        existing.auth = auth
    else:
        db.session.add(PushSubscription(user_id=me, endpoint=endpoint, p256dh=p256dh, auth=auth))
    db.session.commit()

    return jsonify({"message": "Berhasil subscribe push notification."}), 200


@push_bp.route("/unsubscribe", methods=["POST"])
@jwt_required()
def unsubscribe():
    data = request.get_json() or {}
    endpoint = data.get("endpoint")
    if not endpoint:
        return jsonify({"message": "endpoint wajib diisi."}), 400

    PushSubscription.query.filter_by(endpoint=endpoint).delete()
    db.session.commit()
    return jsonify({"message": "Berhasil unsubscribe."}), 200


def send_push_to_user(user_id, title, body, url="/"):
    """Kirim push ke SEMUA device yang pernah subscribe punya user ini.
    Dipanggil dari route lain (misal pas ada chat baru) — bukan endpoint HTTP."""
    if not VAPID_PRIVATE_KEY or not VAPID_PUBLIC_KEY:
        return  # push belum dikonfigurasi (VAPID key belum di-set di env)

    subs = PushSubscription.query.filter_by(user_id=user_id).all()
    payload = json.dumps({"title": title, "body": body, "url": url})

    for sub in subs:
        try:
            webpush(
                subscription_info=sub.to_subscription_info(),
                data=payload,
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims={"sub": VAPID_CLAIMS_SUB},
                ttl=86400,  # antre sampai 24 jam kalau device belum kejangkau pas itu juga
                headers={"Urgency": "high"},
            )
        except WebPushException as e:
            # Subscription kadaluarsa (browser/OS batalin sendiri) -> hapus dari DB
            if e.response is not None and e.response.status_code in (404, 410):
                db.session.delete(sub)
                db.session.commit()
