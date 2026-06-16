from datetime import datetime
from models import db


class MealPlan(db.Model):
    """Stores AI-generated meal plans for each user."""

    __tablename__ = "meal_plans"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    plan_type = db.Column(db.String(10), nullable=False, default="daily")  # daily / weekly
    plan_data = db.Column(db.Text, nullable=False)  # JSON string from Gemini
    total_calories = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Serialize meal plan to dictionary."""
        import json

        try:
            parsed_plan = json.loads(self.plan_data)
        except (json.JSONDecodeError, TypeError):
            parsed_plan = self.plan_data

        return {
            "id": self.id,
            "user_id": self.user_id,
            "plan_type": self.plan_type,
            "plan_data": parsed_plan,
            "total_calories": self.total_calories,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
