from datetime import datetime
from flask_login import UserMixin
from models import db


class User(UserMixin, db.Model):
    """User model for authentication and profile data."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)

    # Profile fields (nullable — filled after registration)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(10), nullable=True)  # male, female, other
    height_cm = db.Column(db.Float, nullable=True)
    weight_kg = db.Column(db.Float, nullable=True)

    # Activity & goals
    activity_level = db.Column(
        db.String(20), nullable=True
    )  # sedentary, lightly_active, moderately_active, very_active, extra_active
    goal = db.Column(
        db.String(20), nullable=True
    )  # weight_loss, weight_gain, maintain, muscle_gain

    # Dietary info
    dietary_preference = db.Column(
        db.String(50), nullable=True
    )  # vegetarian, vegan, keto, none
    allergies = db.Column(db.Text, nullable=True)  # comma-separated

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    meal_plans = db.relationship("MealPlan", backref="user", lazy=True)

    def to_dict(self):
        """Serialize user to dictionary (excludes password)."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "age": self.age,
            "gender": self.gender,
            "height_cm": self.height_cm,
            "weight_kg": self.weight_kg,
            "activity_level": self.activity_level,
            "goal": self.goal,
            "dietary_preference": self.dietary_preference,
            "allergies": self.allergies,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "profile_complete": all(
                [
                    self.age,
                    self.gender,
                    self.height_cm,
                    self.weight_kg,
                    self.activity_level,
                    self.goal,
                ]
            ),
        }
