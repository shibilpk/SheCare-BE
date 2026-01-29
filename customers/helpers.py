def bmi_health_summary(weight_kg, height_cm):
    height_m = height_cm / (100.0)

    # Standard BMI
    bmi = weight_kg / (height_m ** 2)

    # Oxford (New) BMI
    oxford_bmi = 1.3 * (weight_kg / (height_m ** 2.5))

    # Healthy BMI limits
    min_bmi = 18.5
    max_bmi = 25

    # Healthy weight range
    min_weight = min_bmi * (height_m ** 2)
    max_weight = max_bmi * (height_m ** 2)

    notes = [
        "Healthy BMI: 18.5–25 kg/m²",
        f"Healthy weight: {min_weight:.1f}–{max_weight:.1f} kg"
    ]

    # Weight change needed
    change_msg = None
    if weight_kg < min_weight:
        change_msg = (
            f"Gain {min_weight - weight_kg:.1f} kg to reach a healthy weight.")
    elif weight_kg > max_weight:
        change_msg = (
            f"Lose {weight_kg - max_weight:.1f} kg to reach a healthy weight.")
    else:
        change_msg = "You are already within the healthy weight range."

    if change_msg:
        notes.append(change_msg)

    # Oxford BMI status (UNCHANGED logic)
    if oxford_bmi < 16:
        status = "Severe Thinness"
    elif 16 <= oxford_bmi < 17:
        status = "Moderate Thinness"
    elif 17 <= oxford_bmi < 18.5:
        status = "Mild Thinness"
    elif 18.5 <= oxford_bmi < 25:
        status = "Healthy weight"
    elif 25 <= oxford_bmi < 30:
        status = "Overweight"
    elif 30 <= oxford_bmi < 35:
        status = "Obese Class I"
    elif 35 <= oxford_bmi < 40:
        status = "Obese Class II"
    else:
        status = "Morbidly Obese"

    return {
        "bmi": round(bmi, 1),
        "notes": notes,
        "new_bmi": round(oxford_bmi, 1),
        "status": status
    }
