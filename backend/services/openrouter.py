import json
import requests
from flask import current_app


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def get_openrouter_headers():
    """Build auth headers for OpenRouter."""
    api_key = current_app.config.get("OPENROUTER_API_KEY", "")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY is not set in environment variables")
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def build_meal_prompt(user_data: dict, plan_type: str = "daily") -> str:
    """
    Build a detailed prompt to generate a meal plan.

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
    if dietary_pref == "indian_vegetarian":
        dietary_text = "Dietary preference: Gourmet Indian Vegetarian. The meal plan must consist strictly of premium, high-end, and very fancy Indian vegetarian cuisine (e.g., saffron-infused paneer tikka, slow-cooked dal makhani prepared with organic butter, fragrant basmati pulao, cardamom-scented chia kheer, avocado-stuffed gourmet parathas, etc.). Meal names and descriptions must sound premium, appetizing, and specify gourmet presentation and elegant plating instructions."
    elif dietary_pref == "indian_non_vegetarian":
        dietary_text = "Dietary preference: Gourmet Indian Non-Vegetarian. The meal plan must consist strictly of premium, high-end, and very fancy Indian dishes, allowing premium non-vegetarian proteins (e.g., saffron chicken tikka, cardamon-infused lamb shank curry, grilled tandoori salmon, gourmet egg bhurji with truffles, fragrant biryanis, etc.). Meal names and descriptions must sound premium, appetizing, and specify gourmet presentation and elegant plating instructions."
    else:
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


def generate_mock_meal_plan(user_data: dict, plan_type: str = "daily") -> dict:
    """Generate a highly customized fancy meal plan locally as a robust fallback."""
    import random
    
    goal = user_data.get("goal", "maintain")
    pref = user_data.get("dietary_preference", "none")
    
    weight = user_data.get("weight_kg", 70.0) or 70.0
    height = user_data.get("height_cm", 175.0) or 175.0
    age = user_data.get("age", 30) or 30
    gender = user_data.get("gender", "male")
    
    if gender == "male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161
        
    act = user_data.get("activity_level", "moderately_active")
    multipliers = {
        "sedentary": 1.2,
        "lightly_active": 1.375,
        "moderately_active": 1.55,
        "very_active": 1.725,
        "extra_active": 1.9
    }
    tdee = bmr * multipliers.get(act, 1.55)
    
    if goal == "weight_loss":
        target_calories = int(tdee - 500)
    elif goal == "weight_gain":
        target_calories = int(tdee + 500)
    elif goal == "muscle_gain":
        target_calories = int(tdee + 300)
    else:
        target_calories = int(tdee)
        
    target_calories = max(1200, min(4000, target_calories))
    
    if goal == "muscle_gain":
        p_pct, c_pct, f_pct = 0.30, 0.45, 0.25
    elif goal == "weight_loss":
        p_pct, c_pct, f_pct = 0.35, 0.35, 0.30
    else:
        p_pct, c_pct, f_pct = 0.25, 0.50, 0.25
        
    total_protein = int((target_calories * p_pct) / 4)
    total_carbs = int((target_calories * c_pct) / 4)
    total_fat = int((target_calories * f_pct) / 9)
    
    is_veg = pref in ["vegetarian", "vegan", "indian_vegetarian"]
    
    days_to_gen = 7 if plan_type == "weekly" else 1
    days_data = []
    
    indian_veg_meals = [
        # Breakfast
        [
            {"meal_type": "breakfast", "name": "Saffron-Infused Paneer & Avocado Paratha", "ingredients": ["Organic whole wheat flour (60g)", "Aged Paneer (50g)", "Fresh Avocado (0.5 medium)", "A2 cow ghee (1 tsp)", "Spices & Herbs"], "instructions": "Knead dough. Stuff with mashed paneer, avocado, and spices. Roll and cook on a griddle using ghee. Serve hot with organic mint chutney.", "prep_time": "15 min", "calories_pct": 0.25},
            {"meal_type": "breakfast", "name": "Cardamom Spiced Oats Kheer with Berries", "ingredients": ["Steel cut oats (50g)", "Almond milk (250ml)", "Green cardamom powder (0.25 tsp)", "Organic honey (1 tsp)", "Fresh blueberries & saffron strands"], "instructions": "Simmer oats in almond milk with cardamom until creamy. Stir in honey. Garnish with blueberries and saffron.", "prep_time": "12 min", "calories_pct": 0.25},
            {"meal_type": "breakfast", "name": "Gourmet Ragi & Spinach Idlis", "ingredients": ["Finger millet/Ragi flour (40g)", "Semolina (20g)", "Fresh spinach puree (30ml)", "Curd (30g)", "Mustard seeds & curry leaves"], "instructions": "Mix Ragi, semolina, yogurt, and spinach puree. Ferment briefly. Steam in idli molds. Temper with mustard seeds and curry leaves.", "prep_time": "20 min", "calories_pct": 0.25}
        ],
        # Morning snack
        [
            {"meal_type": "morning_snack", "name": "Ghee Roasted Makhana & Almonds", "ingredients": ["Lotus seeds/Makhana (25g)", "Raw almonds (10)", "A2 cow ghee (0.5 tsp)", "Himalayan pink salt & black pepper"], "instructions": "Heat ghee in a pan. Roast makhana and almonds on low heat until crunchy. Season with pink salt and freshly ground pepper.", "prep_time": "5 min", "calories_pct": 0.08},
            {"meal_type": "morning_snack", "name": "Spiced Cucumber & Pomegranate Chaat", "ingredients": ["English cucumber (1 cup diced)", "Fresh pomegranate pearls (0.5 cup)", "Chaat masala (0.5 tsp)", "Fresh mint & lemon juice"], "instructions": "Toss cucumber and pomegranate in a bowl. Drizzle lemon juice and sprinkle chaat masala. Garnish with chopped mint.", "prep_time": "5 min", "calories_pct": 0.08}
        ],
        # Lunch
        [
            {"meal_type": "lunch", "name": "Shahi Paneer Kofta in Cashew-Tomato Gravy", "ingredients": ["Low-fat Paneer (100g)", "Cashew nuts (15g)", "Tomato puree (1 cup)", "Ginger-garlic paste (1 tsp)", "Basmati Rice (60g, raw)", "Organic spices"], "instructions": "Shape paneer into kofta balls. Simmer cashew-tomato paste with aromatics to make gravy. Cook basmati rice separately. Serve hot.", "prep_time": "25 min", "calories_pct": 0.32},
            {"meal_type": "lunch", "name": "Artisanal Black Dal Makhani & Brown Basmati", "ingredients": ["Whole black lentils (50g)", "Red kidney beans (15g)", "A2 cream (1 tbsp)", "White butter (1 tsp)", "Brown Basmati Rice (60g, raw)"], "instructions": "Slow-cook lentils and kidney beans with spices for 4 hours. Finish with cream and butter. Serve alongside steamed brown rice.", "prep_time": "30 min", "calories_pct": 0.32},
            {"meal_type": "lunch", "name": "Smoked Tandoori Gobhi & Moong Dal Khichdi", "ingredients": ["Cauliflower florets (100g)", "Yellow split Moong Dal (40g)", "Quinoa (30g)", "Cow ghee (1 tsp)", "Ginger & whole spices"], "instructions": "Marinate cauliflower in spiced yogurt and roast. Cook moong dal and quinoa khichdi. Top with roasted gobhi and ghee.", "prep_time": "25 min", "calories_pct": 0.32}
        ],
        # Afternoon snack
        [
            {"meal_type": "afternoon_snack", "name": "Premium Pistachio Chia Seed Pudding", "ingredients": ["Black chia seeds (2 tbsp)", "Coconut milk (150ml)", "Slivered pistachios (10g)", "Organic maple syrup (1 tsp)"], "instructions": "Soak chia seeds in coconut milk overnight or for 2 hours. Top with pistachios and drizzle maple syrup before serving.", "prep_time": "5 min (plus soak)", "calories_pct": 0.10},
            {"meal_type": "afternoon_snack", "name": "Rose Petal Almond Meal Halwa", "ingredients": ["Almond flour (30g)", "Warm water (50ml)", "Ghee (1 tsp)", "Stevia", "Edible organic rose petals"], "instructions": "Roast almond flour in ghee. Slowly add water and stevia, stirring continuously until thick. Garnish with rose petals.", "prep_time": "10 min", "calories_pct": 0.10}
        ],
        # Dinner
        [
            {"meal_type": "dinner", "name": "Tandoori Grilled Tofu Tikka & Quinoa Pulao", "ingredients": ["Extra firm Tofu (120g)", "Bell peppers & onions (1 cup)", "Greek yogurt marinade (2 tbsp)", "Quinoa (50g, raw)", "Herbs"], "instructions": "Marinate tofu and veggies, then grill. Cook quinoa pulav with main spices. Serve grilled tikka over quinoa pulav.", "prep_time": "20 min", "calories_pct": 0.25},
            {"meal_type": "dinner", "name": "Kashmiri Methi Chaman & Gluten-free Roti", "ingredients": ["Paneer (80g)", "Fresh fenugreek leaves (1 cup)", "Jowar/Sorghum flour (60g)", "Olive oil (1 tsp)", "Spices"], "instructions": "Cook methi and paneer cubes in Kashmiri style yellow gravy. Prepare jowar rotis on a clay griddle. Serve hot.", "prep_time": "22 min", "calories_pct": 0.25},
            {"meal_type": "dinner", "name": "Artisanal Palak Paneer with Truffle oil drizzle", "ingredients": ["Paneer (100g)", "Spinach leaves (1.5 cups)", "Truffle oil (0.5 tsp)", "Whole wheat phulka (2)", "Onions & garlic"], "instructions": "Blanch and puree spinach. Saute with aromatics. Add paneer cubes. Drizzle truffle oil before serving with hot phulkas.", "prep_time": "20 min", "calories_pct": 0.25}
        ]
    ]

    indian_nonveg_meals = [
        # Breakfast
        [
            {"meal_type": "breakfast", "name": "Truffle Oil Egg Bhurji & Multigrain Toast", "ingredients": ["Organic cage-free eggs (3)", "Onions & green chillies (0.5 cup)", "Truffle oil (0.5 tsp)", "Artisanal multigrain bread (2 slices)"], "instructions": "Scramble eggs with onions, chillies, and spices. Toast bread. Drizzle truffle oil over scrambled eggs and serve.", "prep_time": "10 min", "calories_pct": 0.25},
            {"meal_type": "breakfast", "name": "Saffron Chicken Keema Paratha", "ingredients": ["Minced chicken breast (80g)", "Whole wheat flour (60g)", "Saffron strands (a pinch)", "Ghee (1 tsp)", "Spices"], "instructions": "Cook chicken mince with spices and a touch of saffron milk. Stuff in rolled wheat dough and griddle-fry with ghee.", "prep_time": "20 min", "calories_pct": 0.25}
        ],
        # Morning snack
        [
            {"meal_type": "morning_snack", "name": "Ghee Roasted Makhana & Almonds", "ingredients": ["Lotus seeds/Makhana (25g)", "Raw almonds (10)", "A2 cow ghee (0.5 tsp)", "Himalayan pink salt & black pepper"], "instructions": "Heat ghee in a pan. Roast makhana and almonds on low heat until crunchy. Season with pink salt and freshly ground pepper.", "prep_time": "5 min", "calories_pct": 0.08}
        ],
        # Lunch
        [
            {"meal_type": "lunch", "name": "Saffron Chicken Tikka Biryani (Gourmet)", "ingredients": ["Chicken breast (120g)", "Aged Basmati Rice (60g, raw)", "Greek yogurt (2 tbsp)", "Saffron milk (2 tbsp)", "Caramelized onions"], "instructions": "Marinate and grill chicken tikka. Layer semi-cooked basmati rice with chicken, saffron, and caramelized onions. Dum cook for 15 min.", "prep_time": "30 min", "calories_pct": 0.32},
            {"meal_type": "lunch", "name": "Cardamom Lamb Shank Curry & Brown Basmati", "ingredients": ["Lean lamb meat (100g)", "Green cardamom pods (4)", "Brown Basmati Rice (60g, raw)", "Tomato-onion gravy base", "Ghee (1 tsp)"], "instructions": "Slow cook lamb shank in a rich onion tomato gravy infused with cardamom. Serve with steamed brown basmati rice.", "prep_time": "35 min", "calories_pct": 0.32}
        ],
        # Afternoon snack
        [
            {"meal_type": "afternoon_snack", "name": "Premium Pistachio Chia Seed Pudding", "ingredients": ["Black chia seeds (2 tbsp)", "Coconut milk (150ml)", "Slivered pistachios (10g)", "Organic maple syrup (1 tsp)"], "instructions": "Soak chia seeds in coconut milk overnight or for 2 hours. Top with pistachios and drizzle maple syrup before serving.", "prep_time": "5 min (plus soak)", "calories_pct": 0.10}
        ],
        # Dinner
        [
            {"meal_type": "dinner", "name": "Tandoori Grilled Salmon Tikka & Asparagus", "ingredients": ["Fresh Salmon fillet (130g)", "Asparagus spears (6)", "Lemon & mustard marinade", "Quinoa pulav (40g, raw)"], "instructions": "Marinate salmon with tandoori spices. Grill to perfection. Saute asparagus. Serve alongside light quinoa pulao.", "prep_time": "20 min", "calories_pct": 0.25},
            {"meal_type": "dinner", "name": "Gourmet Murgh Makhani & Whole Wheat Naan", "ingredients": ["Chicken breast (120g)", "Tomato cream gravy (1 cup)", "Butter (1 tsp)", "Whole wheat flour (60g)", "Kasoori methi"], "instructions": "Grill chicken pieces. Cook tomato cashew gravy, finish with butter and fenugreek. Mix chicken. Serve with fresh clay-oven style wheat naan.", "prep_time": "25 min", "calories_pct": 0.25}
        ]
    ]

    standard_meals = [
        # Breakfast
        [
            {"meal_type": "breakfast", "name": "Avocado & Poached Egg Sourdough", "ingredients": ["Artisanal sourdough (1 thick slice)", "Ripe Avocado (0.5)", "Poached eggs (2)", "Microgreens & chili flakes"], "instructions": "Toast sourdough. Mash avocado on toast. Top with poached eggs, chili flakes, and microgreens.", "prep_time": "10 min", "calories_pct": 0.25},
            {"meal_type": "breakfast", "name": "High-Protein Berry Oats Bowl", "ingredients": ["Oats (50g)", "Whey protein powder (30g)", "Mixed organic berries (0.5 cup)", "Chia seeds (1 tsp)", "Almond butter (1 tbsp)"], "instructions": "Cook oats in water. Stir in protein powder. Top with fresh berries, chia seeds, and almond butter.", "prep_time": "8 min", "calories_pct": 0.25}
        ],
        # Morning snack
        [
            {"meal_type": "morning_snack", "name": "Organic Greek Yogurt & Walnuts", "ingredients": ["Plain Greek yogurt 2% (150g)", "Walnut halves (6)", "Honey (0.5 tsp)"], "instructions": "Scoop yogurt into a bowl. Top with crushed walnuts and drizzle honey.", "prep_time": "2 min", "calories_pct": 0.08}
        ],
        # Lunch
        [
            {"meal_type": "lunch", "name": "Grilled Lemon Herb Salmon & Quinoa", "ingredients": ["Salmon fillet (120g)", "Quinoa (50g, raw)", "Steamed asparagus (1 cup)", "Lemon olive oil dressing"], "instructions": "Grill salmon with herbs. Boil quinoa. Steam asparagus. Drizzle lemon olive oil over the platter.", "prep_time": "20 min", "calories_pct": 0.32},
            {"meal_type": "lunch", "name": "Gourmet Turkey & Avocado Wrap", "ingredients": ["Spinach tortilla (1)", "Sliced turkey breast (100g)", "Avocado slices (0.5)", "Mixed baby greens", "Hummus (2 tbsp)"], "instructions": "Spread hummus on tortilla. Layer turkey, avocado, and greens. Roll tightly and slice in half.", "prep_time": "10 min", "calories_pct": 0.32}
        ],
        # Afternoon snack
        [
            {"meal_type": "afternoon_snack", "name": "Artisanal Apple & Almond Butter", "ingredients": ["Honeycrisp apple (1)", "All-natural almond butter (1.5 tbsp)"], "instructions": "Slice apple. Serve with almond butter on the side for dipping.", "prep_time": "3 min", "calories_pct": 0.10}
        ],
        # Dinner
        [
            {"meal_type": "dinner", "name": "Mediterranean Grilled Chicken & Sweet Potato", "ingredients": ["Chicken breast (130g)", "Sweet potato (150g)", "Roasted bell peppers & zucchini (1 cup)", "Extra virgin olive oil (1 tsp)"], "instructions": "Bake sweet potato. Grill chicken with Mediterranean herbs. Roast vegetables. Serve together with a drizzle of olive oil.", "prep_time": "25 min", "calories_pct": 0.25},
            {"meal_type": "dinner", "name": "Seared Flank Steak & Roasted Broccoli", "ingredients": ["Flank steak (120g)", "Broccoli florets (2 cups)", "Garlic herb butter (1 tsp)", "Wild rice (40g, raw)"], "instructions": "Sear flank steak in a skillet. Roast broccoli in oven. Cook wild rice. Serve steak sliced with garlic butter.", "prep_time": "25 min", "calories_pct": 0.25}
        ]
    ]

    if pref == "indian_vegetarian":
        meal_source = indian_veg_meals
    elif pref == "indian_non_vegetarian":
        meal_source = indian_nonveg_meals
    else:
        if is_veg:
            meal_source = indian_veg_meals
        else:
            meal_source = standard_meals

    for d in range(1, days_to_gen + 1):
        day_meals = []
        day_cals = 0
        day_protein = 0
        day_carbs = 0
        day_fat = 0
        
        # Pick random choices from standard templates
        for course in meal_source:
            # pick random index based on day and index so it has variety
            meal_template = course[(d + meal_source.index(course)) % len(course)]
            
            meal_cals = int(target_calories * meal_template["calories_pct"])
            meal_prot = int(total_protein * meal_template["calories_pct"])
            meal_carb = int(total_carbs * meal_template["calories_pct"])
            meal_fats = int(total_fat * meal_template["calories_pct"])
            
            day_meals.append({
                "meal_type": meal_template["meal_type"],
                "name": meal_template["name"],
                "ingredients": meal_template["ingredients"],
                "instructions": meal_template["instructions"],
                "prep_time": meal_template["prep_time"],
                "calories": meal_cals,
                "protein": meal_prot,
                "carbs": meal_carb,
                "fat": meal_fats
            })
            
            day_cals += meal_cals
            day_protein += meal_prot
            day_carbs += meal_carb
            day_fat += meal_fats
            
        day_name = f"Day {d}"
        if plan_type == "weekly":
            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            if d <= 7:
                day_name = day_names[d - 1]
                
        days_data.append({
            "day": day_name,
            "total_calories": day_cals,
            "total_protein": day_protein,
            "total_carbs": day_carbs,
            "total_fat": day_fat,
            "meals": day_meals
        })
        
    return {
        "plan_type": plan_type,
        "days": days_data
    }


def generate_meal_plan(user_data: dict, plan_type: str = "daily") -> dict:
    """
    Generate a meal plan using OpenRouter API. Fallback to local mock generator if error/missing key.
    """
    api_key = current_app.config.get("OPENROUTER_API_KEY", "")
    
    try:
        if not api_key:
            print("No OPENROUTER_API_KEY. Using local gourmet mock generator.")
            return generate_mock_meal_plan(user_data, plan_type)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        prompt = build_meal_prompt(user_data, plan_type)
        model = current_app.config.get("OPENROUTER_MODEL", "google/gemini-2.5-flash")

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert nutritionist. Always respond with valid JSON only, no markdown fences or extra text.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 4096,
        }

        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=25)
        response.raise_for_status()

        result = response.json()
        text = result["choices"][0]["message"]["content"].strip()

        # Parse JSON from the response
        try:
            plan = json.loads(text)
        except json.JSONDecodeError:
            # Fallback: strip markdown fences if present
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

    except Exception as e:
        print(f"Error calling OpenRouter: {e}. Falling back to gourmet mock generator.")
        return generate_mock_meal_plan(user_data, plan_type)

