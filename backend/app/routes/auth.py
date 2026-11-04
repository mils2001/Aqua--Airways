from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from sqlalchemy.exc import IntegrityError

from app.extensions import db, bcrypt
from app.models.user import User


auth_bp = Blueprint("auth", __name__)


def user_data(user):
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active
    }


@auth_bp.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "A valid JSON object is required."
        }), 400

    full_name = data.get("full_name")
    email = data.get("email")
    password = data.get("password")

    if not all([full_name, email, password]):
        return jsonify({
            "status": "error",
            "message": "Full name, email and password are required."
        }), 400

    if not isinstance(full_name, str) or not isinstance(email, str) or not isinstance(password, str):
        return jsonify({
            "status": "error",
            "message": "Invalid registration details."
        }), 400

    full_name = full_name.strip()
    email = email.strip().lower()

    if not full_name or "@" not in email or " " in email:
        return jsonify({
            "status": "error",
            "message": "Provide a valid name and email address."
        }), 400

    if len(password) < 8:
        return jsonify({
            "status": "error",
            "message": "Password must contain at least 8 characters."
        }), 400

    if User.query.filter_by(email=email).first():
        return jsonify({
            "status": "error",
            "message": "An account with this email already exists."
        }), 409

    user = User(
        full_name=full_name,
        email=email,
        password_hash=bcrypt.generate_password_hash(password).decode("utf-8")
    )

    try:
        db.session.add(user)
        db.session.commit()

        return jsonify({
            "status": "success",
            "message": "Account created successfully.",
            "user": user_data(user)
        }), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": "An account with this email already exists."
        }), 409




@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "status": "error",
            "message": "A valid JSON object is required."
        }), 400

    email = data.get("email")
    password = data.get("password")

    if not isinstance(email, str) or not isinstance(password, str):
        return jsonify({
            "status": "error",
            "message": "Email and password are required."
        }), 400

    user = User.query.filter_by(email=email.strip().lower()).first()

    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify({
            "status": "error",
            "message": "Invalid email or password."
        }), 401

    if not user.is_active:
        return jsonify({
            "status": "error",
            "message": "This account is inactive."
        }), 403

    access_token = create_access_token(identity=str(user.id))

    return jsonify({
        "status": "success",
        "message": "Login successful.",
        "access_token": access_token,
        "user": user_data(user)
    }), 200


@auth_bp.route("/api/auth/profile", methods=["GET"])
@jwt_required()
def profile():
    identity = get_jwt_identity()

    try:
        user_id = int(identity)
    except (ValueError, TypeError):
        return jsonify({
            "status": "error",
            "message": "Invalid authentication identity."
        }), 401

    user = db.session.get(User, user_id)

    if not user or not user.is_active:
        return jsonify({
            "status": "error",
            "message": "User account not found or inactive."
        }), 401

    return jsonify({
        "status": "success",
        "user": user_data(user)
    }), 200
