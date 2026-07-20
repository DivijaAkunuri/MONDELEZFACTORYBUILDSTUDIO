#!/usr/bin/env python3
"""Focused backend checks for estimator recalculation inputs.

Verifies /api/estimator/calculate-fast returns different totals/confidence for
the edits involved in the reported UI stale-recalculation bug.
"""

import json
import os
import sys
import urllib.request


BASE_URL = os.environ.get(
    "REACT_APP_BACKEND_URL", "https://predict-calc-1.preview.emergentagent.com"
).rstrip("/")
API_URL = f"{BASE_URL}/api/estimator/calculate-fast"


DEFAULT_INPUTS = {
    "project_name": "Chocolate & Bakery Manufacturing Plant",
    "project_type": "Greenfield",
    "industry_type": "Food",
    "product_category": "Chocolate Plant",
    "location_city": "Hamburg",
    "location_country": "Germany",
    "region": "Europe",
    "continent": "Europe",
    "location_tier": "Metro",
    "building_type": "Industrial Building (RCC + PEB)",
    "length_m": 185,
    "width_m": 100,
    "height_m": 10.5,
    "num_floors": 1,
    "bay_spacing_m": 8,
    "plot_area_sqm": 32000,
    "building_components": [
        "Production Block",
        "Warehouse",
        "Cold Store",
        "Utilities Block",
        "Admin Building",
    ],
    "soil_type": "Medium Dense Sand",
    "sbc_soil_type": "Hard Stone",
    "soil_hardness": "Medium",
    "foundation_type": "Raft Foundation",
    "floor_load_kn": 5.0,
    "column_type": "Steel",
    "roof_type": "PEB + Insulated Panel",
    "seismic_zone": "Zone 0 (Very Low)",
    "wind_zone": "Zone 2",
    "wind_speed_ms": 24,
    "gwt_depth": "Medium (3-8 m)",
    "utility_scope": [
        "Boiler House",
        "Chiller Plant",
        "HVAC System",
        "Air Compressors",
        "Water Treatment Plant",
        "Fire Fighting System",
        "Electrical Substation",
    ],
    "production_capacity_tpd": 120,
    "annual_output_mt": 36000,
    "cooling_tunnel_load_tr": 180,
    "tempering_utility_demand": "Medium",
    "humidity_controlled_pct": 40,
    "chocolate_storage_temp_c": 16,
    "process_hot_water_lph": 2500,
    "oven_capacity_kg_hr": 1200,
    "fuel_type": "PNG",
    "baking_line_qty": 2,
    "compressed_air_demand_cfm": 1500,
    "dust_collection_required": True,
    "cooling_conveyor_load": "Standard",
    "include_roads": True,
    "include_landscaping": True,
    "include_fence": True,
    "land_area_sqm": 32000,
    "ground_coverage_pct": 58,
    "far_fsi": 1.2,
    "water_availability": "Municipal + Borewell",
    "grid_reliability": "Good",
    "ambient_temp_range": "Temperate (5°C - 30°C)",
    "relative_humidity_pct": 70,
    "complexity": {
        "seismic_zone_high": False,
        "high_humidity": False,
        "cold_region": False,
        "brownfield": False,
        "gmp_hygienic": True,
        "explosion_risk": False,
        "utility_redundancy": True,
        "high_floor_load": False,
        "remote_site": False,
    },
    "currency": "USD",
    "base_unit": "mm",
    "contingency_pct": 8.0,
}


def post_calc(payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        API_URL, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def clone(**updates):
    payload = json.loads(json.dumps(DEFAULT_INPUTS))
    for key, val in updates.items():
        if key == "complexity_update":
            payload["complexity"].update(val)
        else:
            payload[key] = val
    return payload


def total(result):
    return result["totals"]["total_project_cost"]


def confidence(result):
    return result["totals"]["confidence_score"]


def main():
    checks = []
    base = post_calc(DEFAULT_INPUTS)
    length = post_calc(clone(length_m=300))
    foundation = post_calc(clone(foundation_type="Pile Foundation"))
    contingency = post_calc(clone(contingency_pct=15.0))
    india = post_calc(clone(region="India / South Asia"))
    eur = post_calc(clone(currency="EUR"))
    retrofit = post_calc(clone(project_type="Retrofit / Capacity Upgrade"))
    brownfield = post_calc(clone(project_type="Brownfield / Expansion"))
    remote = post_calc(clone(location_tier="Remote"))
    brownfield_complexity = post_calc(
        clone(project_type="Brownfield / Expansion", complexity_update={"brownfield": True})
    )

    checks.append(("length edit changes total", total(length) != total(base)))
    checks.append(("pile foundation changes total", total(foundation) != total(base)))
    checks.append(("15% contingency changes total", total(contingency) != total(base)))
    checks.append(("India region lowers total", total(india) < total(base)))
    checks.append(("EUR leaves USD total unchanged", total(eur) == total(base)))
    checks.append(("Retrofit confidence is 88", confidence(retrofit) == 88))
    checks.append(("Brownfield confidence is 86", confidence(brownfield) == 86))
    checks.append(("Remote confidence is 88", confidence(remote) == 88))
    checks.append(
        (
            "Brownfield complexity lowers confidence further",
            confidence(brownfield_complexity) < confidence(brownfield),
        )
    )

    print(json.dumps({
        "api_url": API_URL,
        "totals": {
            "base": total(base),
            "length_300": total(length),
            "pile_foundation": total(foundation),
            "contingency_15": total(contingency),
            "india_region": total(india),
            "eur_currency": total(eur),
        },
        "confidence": {
            "base": confidence(base),
            "retrofit": confidence(retrofit),
            "brownfield": confidence(brownfield),
            "remote": confidence(remote),
            "brownfield_plus_complexity": confidence(brownfield_complexity),
        },
        "checks": [{"name": name, "passed": passed} for name, passed in checks],
    }, indent=2))

    if not all(passed for _, passed in checks):
        sys.exit(1)


if __name__ == "__main__":
    main()