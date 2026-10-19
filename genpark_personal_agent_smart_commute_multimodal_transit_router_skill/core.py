# -*- coding: utf-8 -*-
"""Smart Commute Multimodal Transit Router Skill for GenPark Personal Agents."""
import json
from datetime import datetime, timedelta
from typing import Dict, Any

def calculate_optimal_commute_route(origin_zone: str, destination_zone: str, target_arrival_time_iso: str, transit_incident_reported: bool = False, rain_precipitation_pct: int = 10) -> Dict[str, Any]:
    options = []

    # Option A: Rail Transit
    rail_delay = 25 if transit_incident_reported else 0
    rail_travel_mins = 35 + rail_delay
    options.append({
        "mode": "METRO_RAIL",
        "total_duration_minutes": rail_travel_mins,
        "monetary_cost_usd": 2.90,
        "reliability_score_pct": 55 if transit_incident_reported else 94,
        "is_recommended": not transit_incident_reported and rain_precipitation_pct > 40
    })

    # Option B: Micro-mobility + Express Bus
    bike_bus_mins = 38
    is_weather_viable = rain_precipitation_pct < 35
    options.append({
        "mode": "E_BIKE_TO_EXPRESS_BUS",
        "total_duration_minutes": bike_bus_mins,
        "monetary_cost_usd": 4.50,
        "reliability_score_pct": 88 if is_weather_viable else 45,
        "is_recommended": transit_incident_reported and is_weather_viable
    })

    # Option C: Direct Rideshare
    rideshare_mins = 28
    options.append({
        "mode": "RIDESHARE_DIRECT",
        "total_duration_minutes": rideshare_mins,
        "monetary_cost_usd": 28.50,
        "reliability_score_pct": 92,
        "is_recommended": transit_incident_reported and not is_weather_viable
    })

    recommended_option = next((opt for opt in options if opt["is_recommended"]), options[0])

    try:
        parts = target_arrival_time_iso.split(":")
        arr_dt = datetime.now().replace(hour=int(parts[0]), minute=int(parts[1]), second=0)
        dep_dt = arr_dt - timedelta(minutes=recommended_option["total_duration_minutes"] + 10)
        departure_str = dep_dt.strftime("%H:%M")
    except Exception:
        departure_str = "T-45min"

    return {
        "origin": origin_zone,
        "destination": destination_zone,
        "target_arrival": target_arrival_time_iso,
        "suggested_departure_time": departure_str,
        "recommended_modal_choice": recommended_option["mode"],
        "contingency_reasoning": "Subway service interruption detected; shifted to multimodal e-bike + express bus arterial route." if transit_incident_reported else "Subway network running at optimal frequency.",
        "evaluated_modalities": options,
        "dispatcher": "GenPark Urban Mobility Sentinel"
    }

def evaluate_rideshare_surge_bypass(current_surge_multiplier: float, base_trip_cost_usd: float, walking_minutes_to_perimeter: int = 5) -> Dict[str, Any]:
    surged_fare = round(base_trip_cost_usd * current_surge_multiplier, 2)
    standard_fare = round(base_trip_cost_usd, 2)
    savings_usd = round(surged_fare - standard_fare, 2)

    # Imputed hourly earning rate from walking
    hourly_rate_saved = round((savings_usd / max(1, walking_minutes_to_perimeter)) * 60, 2)

    return {
        "current_surge_fare_usd": surged_fare,
        "perimeter_fare_usd": standard_fare,
        "potential_savings_usd": savings_usd,
        "walking_duration_minutes": walking_minutes_to_perimeter,
        "effective_earning_rate_per_hour_usd": hourly_rate_saved,
        "recommendation": f"Walk {walking_minutes_to_perimeter} minutes outside the stadium surge geo-fence to save ${savings_usd:.2f} (equivalent to ${hourly_rate_saved:.2f}/hr value).",
        "is_arbitrage_worthwhile": savings_usd >= 12.0
    }
