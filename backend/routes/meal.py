import json
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db
from models.meal_plan import MealPlan
from services.openrouter import generate_meal_plan
from services.bmi import calculate_bmi

meal_bp = Blueprint("meal", __name__, url_prefix="/api/meal")


@meal_bp.route("/generate", methods=["POST"])
@login_required
def generate():
    """Generate a new AI meal plan for the current user."""
    # Check that profile is complete
    if not all(
        [
            current_user.age,
            current_user.gender,
            current_user.height_cm,
            current_user.weight_kg,
            current_user.activity_level,
            current_user.goal,
        ]
    ):
        return jsonify({"error": "Please complete your profile before generating a meal plan"}), 400

    data = request.get_json() or {}
    plan_type = data.get("plan_type", "daily")

    if plan_type not in ["daily", "weekly"]:
        return jsonify({"error": "plan_type must be 'daily' or 'weekly'"}), 400

    # Build user data for the prompt
    bmi_data = calculate_bmi(current_user.weight_kg, current_user.height_cm)

    user_data = {
        "age": current_user.age,
        "gender": current_user.gender,
        "height_cm": current_user.height_cm,
        "weight_kg": current_user.weight_kg,
        "bmi": bmi_data.get("bmi", "N/A"),
        "activity_level": current_user.activity_level,
        "goal": current_user.goal,
        "dietary_preference": current_user.dietary_preference or "none",
        "allergies": current_user.allergies or "",
    }

    try:
        plan = generate_meal_plan(user_data, plan_type)
    except Exception as e:
        return jsonify({"error": f"Failed to generate meal plan: {str(e)}"}), 500

    # Calculate total calories from the plan
    total_calories = 0
    if "days" in plan:
        for day in plan["days"]:
            total_calories += day.get("total_calories", 0)
        if plan_type == "daily" and plan["days"]:
            total_calories = plan["days"][0].get("total_calories", 0)

    # Save to database
    meal_plan = MealPlan(
        user_id=current_user.id,
        plan_type=plan_type,
        plan_data=json.dumps(plan),
        total_calories=total_calories,
    )
    db.session.add(meal_plan)
    db.session.commit()

    return jsonify({"message": "Meal plan generated", "meal_plan": meal_plan.to_dict()}), 201


@meal_bp.route("/history", methods=["GET"])
@login_required
def history():
    """Get all meal plans for the current user, newest first."""
    plans = (
        MealPlan.query.filter_by(user_id=current_user.id)
        .order_by(MealPlan.created_at.desc())
        .all()
    )
    return jsonify({"meal_plans": [p.to_dict() for p in plans]}), 200


@meal_bp.route("/<int:plan_id>", methods=["GET"])
@login_required
def get_plan(plan_id):
    """Get a specific meal plan by ID."""
    plan = MealPlan.query.filter_by(id=plan_id, user_id=current_user.id).first()

    if not plan:
        return jsonify({"error": "Meal plan not found"}), 404

    return jsonify({"meal_plan": plan.to_dict()}), 200
