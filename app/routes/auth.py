from flask import Blueprint, request, jsonify
from app import db
from app.models.user import User
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.utils.decorators import role_required

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    nama = data.get('nama')
    email = data.get('email')
    password = data.get('password')
    no_hp = data.get('no_hp')
    role = data.get('role', 'customer')

    if not nama or not email or not password:
        return jsonify({"message": "nama, email, dan password wajib diisi"}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"message": "Email has been registered."}), 409

    new_user = User(nama=nama, email=email, no_hp=no_hp, role=role)
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "message" : "Succesfully Registered",
        "user": new_user.to_dict()
    }), 201

@auth_bp.route("/login", methods=['POST'])
def login():
    data = request.get_json()

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"message" :"Email and Password must be filled"}), 400
    
    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({'message':'Email or Password maybe Wrong'}), 401

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role}
    )
    return jsonify({
        "message": 'Login Success!',
        'access_tokes' : access_token,
        "user": user.to_dict()
    }), 200

@auth_bp.route("/me", methods=['GET'])
@jwt_required()
def get_me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({
            "message" : 'User not found'
        }), 404
    return jsonify({
        "user" : user.to_dict()
    }), 200

@auth_bp.route("/admin-only", methods=['GET'])
@role_required("super_admin", "organizer")
def admin_only():
    return jsonify({
        "message": "You have been succes for accessing admin/organizer endpoint!"
    })