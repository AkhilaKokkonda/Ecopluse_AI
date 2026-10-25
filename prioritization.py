
def prioritize_issue(
    category,
    severity,
    safety_risk,
    resource_loss=0,
    unresolved_hours=0,
    near_electrical=False,
):
    severity = max(1, min(int(severity), 5))
    safety_risk = max(1, min(int(safety_risk), 5))
    resource_loss = max(0, float(resource_loss))
    unresolved_hours = max(0, float(unresolved_hours))

    score = (
        (severity / 5) * 35
        + (safety_risk / 5) * 30
        + min(resource_loss / 100, 1) * 25
        + min(unresolved_hours / 48, 1) * 10
    )

    reasons = [
        f"Reported severity: {severity}/5",
        f"Safety risk: {safety_risk}/5",
    ]

    if resource_loss > 0:
        reasons.append("Resource loss was included in the priority score.")

    if unresolved_hours > 0:
        reasons.append("Time unresolved was included in the priority score.")

    if category == "Water Leakage":
        action = "Inspect the leak and isolate the water supply if necessary."
    elif category == "Overflowing Tank":
        action = "Inspect the tank float valve and stop overflow safely."
    elif category == "Electricity Wastage":
        action = "Inspect the affected electrical equipment safely."
    elif category == "Lighting or Fan Left On":
        action = "Check whether unused lights and fans can be switched off."
    elif category == "Waste Management":
        action = "Arrange waste segregation and appropriate collection."
    elif category == "Single-Use Plastic":
        action = "Replace disposable items with reusable alternatives."
    else:
        action = "Inspect the reported issue and determine an appropriate action."

    if near_electrical and category in (
        "Water Leakage",
        "Overflowing Tank",
    ):
        score = 100
        priority = "Critical"
        reasons.append(
            "Water near electrical equipment requires urgent safety assessment."
        )
        action = (
            "Keep people away and notify authorized facilities staff. "
            "Do not touch wet electrical equipment."
        )
    elif safety_risk == 5:
        priority = "Critical"
        reasons.append("Maximum safety-risk rating.")
    elif score >= 70:
        priority = "High"
    elif score >= 40:
        priority = "Medium"
    else:
        priority = "Low"

    return {
        "priority_score": round(min(score, 100), 2),
        "priority_level": priority,
        "priority_reasons": reasons,
        "recommended_action": action,
    }
