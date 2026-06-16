from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from models import db
from models.user import User

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
bcrypt = Bcrypt()


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user with name, email, and password."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    # Validation
    if not name or not email or not password:
        return jsonify({"error": "Name, email, and password are required"}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    # Check if user exists
    existing = User.query.filter_by(email=email).first()
    if existing:
        return jsonify({"error": "An account with this email already exists"}), 409

    # Create user
    password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
    user = User(name=name, email=email, password_hash=password_hash)

    db.session.add(user)
    db.session.commit()

    login_user(user, remember=True)

    return jsonify({"message": "Registration successful", "user": user.to_dict()}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """Login with email and password."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid email or password"}), 401

    remember = data.get("remember", False)
    login_user(user, remember=remember)

    return jsonify({"message": "Login successful", "user": user.to_dict()}), 200


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """Logout the current user."""
    logout_user()
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route("/me", methods=["GET"])
@login_required
def me():
    """Get the current authenticated user."""
    return jsonify({"user": current_user.to_dict()}), 200
