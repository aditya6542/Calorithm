def calculate_bmi(weight_kg: float, height_cm: float) -> dict:
    """
    Calculate BMI and return value, category, and healthy weight range.

    Args:
        weight_kg: Weight in kilograms
        height_cm: Height in centimeters

    Returns:
        Dictionary with bmi, category, and healthy_weight_range
    """
    if not weight_kg or not height_cm or height_cm <= 0 or weight_kg <= 0:
        return {"error": "Valid weight and height are required"}

    height_m = height_cm / 100
    bmi = round(weight_kg / (height_m ** 2), 1)

    # Determine category
    if bmi < 18.5:
        category = "Underweight"
        color = "#f0ad4e"
    elif bmi < 25:
        category = "Normal"
        color = "#00d68f"
    elif bmi < 30:
        category = "Overweight"
        color = "#ff6b35"
    else:
        category = "Obese"
        color = "#ff4757"

    # Healthy weight range for their height (BMI 18.5–24.9)
    healthy_min = round(18.5 * (height_m ** 2), 1)
    healthy_max = round(24.9 * (height_m ** 2), 1)

    return {
        "bmi": bmi,
        "category": category,
        "color": color,
        "healthy_weight_range": {"min_kg": healthy_min, "max_kg": healthy_max},
        "height_cm": height_cm,
        "weight_kg": weight_kg,
    }
