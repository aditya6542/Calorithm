import json
from google import genai
from flask import current_app


def get_gemini_client():
    """Get a configured Gemini client."""
    api_key = current_app.config.get("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in environment variables")
    return genai.Client(api_key=api_key)


def build_meal_prompt(user_data: dict, plan_type: str = "daily") -> str:
    """
    Build a detailed prompt for Gemini to generate a meal plan.

    Args:
        user_data: Dictionary with user profile info
        plan_type: 'daily' or 'weekly'
    """
    goal_descriptions = {
        "weight_loss": "lose weight with a caloric deficit",
        "weight_gain": "gain weight with a caloric surplus",
        "maintain": "maintain their current weight",
        "muscle_gain": "build muscle with high protein intake",
    }

    activity_descriptions = {
        "sedentary": "little or no exercise",
        "lightly_active": "light exercise 1-3 days/week",
        "moderately_active": "moderate exercise 3-5 days/week",
        "very_active": "hard exercise 6-7 days/week",
        "extra_active": "very hard exercise, physical job, or training twice a day",
    }

    goal_text = goal_descriptions.get(user_data.get("goal", ""), "maintain their current weight")
    activity_text = activity_descriptions.get(
        user_data.get("activity_level", ""), "moderate activity"
    )

    dietary_pref = user_data.get("dietary_preference", "none")
    dietary_text = (
        f"Dietary preference: {dietary_pref}."
        if dietary_pref and dietary_pref != "none"
        else "No specific dietary restrictions."
    )

    allergies = user_data.get("allergies", "")
    allergy_text = (
        f"Food allergies/intolerances: {allergies}. AVOID these ingredients completely."
        if allergies
        else "No known food allergies."
    )

    duration = "one day (today)" if plan_type == "daily" else "a full week (Monday to Sunday)"

    prompt = f"""You are an expert nutritionist and certified dietitian. Create a personalized meal plan for {duration}.

**Client Profile:**
- Age: {user_data.get('age', 'not specified')} years old
- Gender: {user_data.get('gender', 'not specified')}
- Height: {user_data.get('height_cm', 'not specified')} cm
- Weight: {user_data.get('weight_kg', 'not specified')} kg
- BMI: {user_data.get('bmi', 'not calculated')}
- Activity Level: {activity_text}
- Goal: {goal_text}
- {dietary_text}
- {allergy_text}

**Requirements:**
1. Include breakfast, morning snack, lunch, afternoon snack, dinner, and an optional evening snack
2. Each meal must include: meal name, list of ingredients with quantities, preparation instructions, estimated prep time, calories, protein (g), carbs (g), and fat (g)
3. Ensure the total daily calories align with the client's goal
4. Make meals practical, delicious, and easy to prepare
5. Include variety — don't repeat the same meals

**IMPORTANT: Return ONLY valid JSON in exactly this format, no other text:**

{{"plan_type": "{plan_type}", "days": [
  {{"day": "Day 1", "total_calories": 2000, "total_protein": 120, "total_carbs": 200, "total_fat": 70,
    "meals": [
      {{"meal_type": "breakfast", "name": "Meal Name", "ingredients": ["ingredient 1", "ingredient 2"],
        "instructions": "Step by step instructions", "prep_time": "15 min",
        "calories": 400, "protein": 30, "carbs": 40, "fat": 15
      }}
    ]
  }}
]}}
"""
    return prompt


def generate_meal_plan(user_data: dict, plan_type: str = "daily") -> dict:
    """
    Generate a meal plan using Gemini API.

    Args:
        user_data: Dictionary with user profile information
        plan_type: 'daily' or 'weekly'

    Returns:
        Parsed meal plan dictionary
    """
    client = get_gemini_client()
    prompt = build_meal_prompt(user_data, plan_type)

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "temperature": 0.7,
        },
    )

    try:
        plan = json.loads(response.text)
    except json.JSONDecodeError:
        # Fallback: try to extract JSON from the response
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        plan = json.loads(text.strip())

    # Calculate total calories if not present
    if "days" in plan:
        for day in plan["days"]:
            if "total_calories" not in day or not day["total_calories"]:
                day["total_calories"] = sum(
                    meal.get("calories", 0) for meal in day.get("meals", [])
                )

    return plan
