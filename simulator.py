
def simulate_water(leakage_litres_per_hour=5, hours_avoided=24):
    if leakage_litres_per_hour < 0 or hours_avoided < 0:
        raise ValueError("Inputs cannot be negative.")

    litres_saved = leakage_litres_per_hour * hours_avoided

    return {
        "litres_saved": round(litres_saved, 2),
        "leakage_litres_per_hour": leakage_litres_per_hour,
        "hours_avoided": hours_avoided,
        "formula": "Leakage rate × hours avoided",
        "is_estimate": True,
    }


def simulate_electricity(
    power_kw_per_device=0.5,
    device_count=1,
    hours_avoided=1,
    tariff_per_kwh=8,
    emission_factor=0.7,
):
    values = (
        power_kw_per_device,
        device_count,
        hours_avoided,
        tariff_per_kwh,
        emission_factor,
    )

    if any(value < 0 for value in values):
        raise ValueError("Inputs cannot be negative.")

    energy_saved = power_kw_per_device * device_count * hours_avoided
    cost_saved = energy_saved * tariff_per_kwh
    emissions_avoided = energy_saved * emission_factor

    return {
        "energy_saved_kwh": round(energy_saved, 2),
        "cost_saved": round(cost_saved, 2),
        "emissions_avoided_kg_co2e": round(emissions_avoided, 2),
        "formula": "Power × devices × hours avoided",
        "tariff_per_kwh": tariff_per_kwh,
        "emission_factor_kg_co2e_per_kwh": emission_factor,
        "is_estimate": True,
    }


def simulate_plastic(items_avoided):
    if not isinstance(items_avoided, int) or items_avoided < 0:
        raise ValueError("Items avoided must be a non-negative integer.")

    return {
        "single_use_items_avoided": items_avoided,
        "is_estimate": True,
    }
