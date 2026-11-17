from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db
from models import User


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():

    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({
            "message": "Name, email and password are required."
        }), 400

    existing_user = User.query.filter_by(email=email).first()

    if existing_user:
        return jsonify({
            "message": "Email already registered."
        }), 409

    user = User(
        name=name,
        email=email,
        password=generate_password_hash(password),
        role="user",
        status="approved"
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({
        "message": "User registered successfully."
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({
            "message": "Email and password are required."
        }), 400

    user = User.query.filter_by(email=email).first()

    if user is None:
        return jsonify({
            "message": "Invalid email or password."
        }), 401

    if not check_password_hash(user.password, password):
        return jsonify({
            "message": "Invalid email or password."
        }), 401

    if user.status == "blacklisted":
        return jsonify({
            "message": "Your account has been blacklisted."
        }), 403

    if user.role == "staff" and user.status != "approved":
        return jsonify({
            "message": "Your staff account is not approved yet."
        }), 403

    session.clear()
    session["user_id"] = user.id
    session["role"] = user.role

    return jsonify({
        "message": "Login successful.",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "status": user.status
        }
    }), 200

@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()

    return jsonify({
        "message": "Logout successful."
    }), 200
@auth_bp.route("/me", methods=["GET"])
def current_user():

    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "message": "Please login first."
        }), 401

    user = db.session.get(User, user_id)

    if user is None or user.status != "approved":
        session.clear()

        return jsonify({
            "message": "Session is no longer valid."
        }), 401

    return jsonify({
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "status": user.status
        }
    }), 200