from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db
from models.user import User
from services.bmi import calculate_bmi

profile_bp = Blueprint("profile", __name__, url_prefix="/api/profile")

VALID_ACTIVITY_LEVELS = [
    "sedentary",
    "lightly_active",
    "moderately_active",
    "very_active",
    "extra_active",
]
VALID_GOALS = ["weight_loss", "weight_gain", "maintain", "muscle_gain"]
VALID_DIETS = ["vegetarian", "vegan", "keto", "paleo", "none", "indian_vegetarian", "indian_non_vegetarian"]
VALID_GENDERS = ["male", "female", "other"]


@profile_bp.route("", methods=["GET"])
@login_required
def get_profile():
    """Get the current user's profile."""
    return jsonify({"user": current_user.to_dict()}), 200


@profile_bp.route("", methods=["PUT"])
@login_required
def update_profile():
    """Update the current user's profile information."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    user = User.query.get(current_user.id)

    # Update fields if provided
    if "age" in data:
        age = data["age"]
        if age is not None and (not isinstance(age, int) or age < 1 or age > 150):
            return jsonify({"error": "Age must be between 1 and 150"}), 400
        user.age = age

    if "gender" in data:
        gender = data["gender"]
        if gender and gender not in VALID_GENDERS:
            return jsonify({"error": f"Gender must be one of: {', '.join(VALID_GENDERS)}"}), 400
        user.gender = gender

    if "height_cm" in data:
        height = data["height_cm"]
        if height is not None and (height < 50 or height > 300):
            return jsonify({"error": "Height must be between 50 and 300 cm"}), 400
        user.height_cm = height

    if "weight_kg" in data:
        weight = data["weight_kg"]
        if weight is not None and (weight < 10 or weight > 500):
            return jsonify({"error": "Weight must be between 10 and 500 kg"}), 400
        user.weight_kg = weight

    if "activity_level" in data:
        level = data["activity_level"]
        if level and level not in VALID_ACTIVITY_LEVELS:
            return jsonify(
                {"error": f"Activity level must be one of: {', '.join(VALID_ACTIVITY_LEVELS)}"}
            ), 400
        user.activity_level = level

    if "goal" in data:
        goal = data["goal"]
        if goal and goal not in VALID_GOALS:
            return jsonify({"error": f"Goal must be one of: {', '.join(VALID_GOALS)}"}), 400
        user.goal = goal

    if "dietary_preference" in data:
        pref = data["dietary_preference"]
        if pref and pref not in VALID_DIETS:
            return jsonify(
                {"error": f"Dietary preference must be one of: {', '.join(VALID_DIETS)}"}
            ), 400
        user.dietary_preference = pref

    if "allergies" in data:
        user.allergies = data["allergies"]

    if "name" in data:
        name = data["name"].strip()
        if name:
            user.name = name

    db.session.commit()

    return jsonify({"message": "Profile updated", "user": user.to_dict()}), 200


@profile_bp.route("/bmi", methods=["GET"])
@login_required
def get_bmi():
    """Calculate and return BMI for the current user."""
    if not current_user.weight_kg or not current_user.height_cm:
        return jsonify({"error": "Height and weight are required to calculate BMI"}), 400

    result = calculate_bmi(current_user.weight_kg, current_user.height_cm)
    return jsonify(result), 200
