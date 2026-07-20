#!/usr/bin/env python3
"""Focused API verification for estimator recalculation bug.

Checks calculate-fast/calculate/insights endpoints and verifies edited inputs
change totals, breakdown, utilities, BOQ and confidence values.
"""
import json
import os
import time
from copy import deepcopy

import requests


BASE = os.environ.get("REACT_APP_BACKEND_URL", "https://predict-calc-1.preview.emergentagent.com").rstrip("/")
API = f"{BASE}/api"

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
    "building_components": ["Production Block", "Warehouse", "Cold Store", "Utilities Block", "Admin Building"],
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
    "utility_scope": ["Boiler House", "Chiller Plant", "HVAC System", "Air Compressors", "Water Treatment Plant", "Fire Fighting System", "Electrical Substation"],
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


def post(path, body, timeout=65):
    start = time.perf_counter()
    r = requests.post(f"{API}{path}", json=body, timeout=timeout)
    elapsed = time.perf_counter() - start
    r.raise_for_status()
    return r.json(), elapsed


def assert_shape(result):
    required = ["totals", "breakdown", "boq", "top_cost_items", "utilities", "utilities_total", "utility_demand", "cost_trend"]
    for key in required:
        assert key in result, f"missing key {key}"
    totals = result["totals"]
    for key in ["total_project_cost", "cost_per_sqm", "duration_months", "confidence_score", "contingency", "region_benchmark_delta_pct"]:
        assert key in totals, f"missing totals.{key}"


def main():
    report = {"base_url": BASE, "checks": []}

    baseline, fast_s = post("/estimator/calculate-fast", DEFAULT_INPUTS, timeout=20)
    assert_shape(baseline)
    report["checks"].append({
        "name": "calculate-fast baseline",
        "elapsed_s": round(fast_s, 3),
        "total": baseline["totals"]["total_project_cost"],
        "confidence": baseline["totals"]["confidence_score"],
        "live_source": baseline.get("live_rate_index", {}).get("source"),
    })
    assert fast_s < 3, f"calculate-fast took too long: {fast_s:.2f}s"

    edited = deepcopy(DEFAULT_INPUTS)
    # Include global + structural edits so totals, confidence, benchmark, utility
    # numbers, BOQ, and breakdown percentages all have reason to change.
    edited.update({
        "project_type": "Retrofit / Capacity Upgrade",
        "region": "Asia",
        "industry_type": "FMCG",
        "foundation_type": "Isolated Footing",
    })
    edited_result, edited_s = post("/estimator/calculate-fast", edited, timeout=20)
    assert_shape(edited_result)
    report["checks"].append({
        "name": "calculate-fast edited material fields",
        "elapsed_s": round(edited_s, 3),
        "total": edited_result["totals"]["total_project_cost"],
        "cost_per_sqm": edited_result["totals"]["cost_per_sqm"],
        "confidence": edited_result["totals"]["confidence_score"],
        "benchmark": edited_result["totals"]["region_benchmark_delta_pct"],
        "breakdown_pcts": [b["pct"] for b in edited_result["breakdown"]],
        "utilities_total": edited_result["utilities_total"],
        "first_boq": edited_result["top_cost_items"][0],
    })
    assert edited_result["totals"]["total_project_cost"] != baseline["totals"]["total_project_cost"], "edited total did not change"
    assert edited_result["totals"]["cost_per_sqm"] != baseline["totals"]["cost_per_sqm"], "edited cost/m2 did not change"
    assert edited_result["totals"]["confidence_score"] != baseline["totals"]["confidence_score"], "edited confidence did not change"
    assert edited_result["totals"]["region_benchmark_delta_pct"] != baseline["totals"]["region_benchmark_delta_pct"], "edited benchmark did not change"
    assert [b["pct"] for b in edited_result["breakdown"]] != [b["pct"] for b in baseline["breakdown"]], "breakdown percentages did not change"
    assert edited_result["utilities_total"] != baseline["utilities_total"], "utilities total did not change"
    assert edited_result["top_cost_items"][0]["amount"] != baseline["top_cost_items"][0]["amount"], "BOQ amount did not change"

    second = deepcopy(edited)
    second["foundation_type"] = "Pile Foundation"
    second_result, second_s = post("/estimator/calculate-fast", second, timeout=20)
    assert_shape(second_result)
    report["checks"].append({
        "name": "calculate-fast second edit foundation",
        "elapsed_s": round(second_s, 3),
        "total": second_result["totals"]["total_project_cost"],
        "foundation": second["foundation_type"],
    })
    assert second_result["totals"]["total_project_cost"] != edited_result["totals"]["total_project_cost"], "second edit total did not change"

    # Specific confidence proof: values may be one lower if live material index fallback is active.
    conf_cases = []
    for label, mutator, expected_drop in [
        ("retrofit", lambda x: x.update({"project_type": "Retrofit / Capacity Upgrade"}), 4),
        ("brownfield_project", lambda x: x.update({"project_type": "Brownfield / Expansion"}), 6),
        ("remote_tier", lambda x: x.update({"location_tier": "Remote"}), 4),
        ("brownfield_complexity", lambda x: x["complexity"].update({"brownfield": True}), 3),
    ]:
        case = deepcopy(DEFAULT_INPUTS)
        mutator(case)
        res, _ = post("/estimator/calculate-fast", case, timeout=20)
        actual_drop = baseline["totals"]["confidence_score"] - res["totals"]["confidence_score"]
        conf_cases.append({"case": label, "confidence": res["totals"]["confidence_score"], "drop_from_baseline": actual_drop})
        assert actual_drop == expected_drop, f"{label} confidence drop expected {expected_drop}, got {actual_drop}"
    report["checks"].append({"name": "confidence changes by scenario", "cases": conf_cases})

    calc_result, calc_s = post("/estimator/calculate", DEFAULT_INPUTS, timeout=65)
    assert_shape(calc_result)
    assert "insights" in calc_result and isinstance(calc_result["insights"].get("assumptions"), list), "calculate missing insights"
    report["checks"].append({"name": "calculate full", "elapsed_s": round(calc_s, 3), "has_insights": True})

    insights, ins_s = post("/estimator/insights", {"inputs": edited, "result": edited_result}, timeout=25)
    for key in ["assumptions", "risks", "optimizations", "executive_summary", "source"]:
        assert key in insights, f"insights missing {key}"
    assert ins_s < 20, f"insights took {ins_s:.2f}s"
    report["checks"].append({"name": "insights endpoint", "elapsed_s": round(ins_s, 3), "source": insights.get("source")})

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()