#!/usr/bin/env python3
"""Iteration 3 focused API verification for estimator recalculation/live-rate bug.

Contract under test: editable estimator inputs must influence USD total_project_cost
when they are cost-driving fields; utility_scope must drive utilities_total; currency
and base_unit must be display-only and not alter underlying USD totals.
"""
import json
import os
from copy import deepcopy
from pathlib import Path

import requests


def backend_api_base() -> str:
    env_path = Path("/app/frontend/.env")
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("REACT_APP_BACKEND_URL="):
                return line.split("=", 1)[1].strip().strip('"').rstrip("/") + "/api"
    return os.environ.get("REACT_APP_BACKEND_URL", "https://predict-calc-1.preview.emergentagent.com").rstrip("/") + "/api"


BASE_URL = backend_api_base()

DEFAULT_BODY = {
    "project_name": "Chocolate & Bakery Manufacturing Plant",
    "project_type": "Greenfield",
    "industry_type": "Food",
    "product_category": "Chocolate",
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


def patch_body(patch: dict) -> dict:
    body = deepcopy(DEFAULT_BODY)
    body.update(patch)
    return body


def post_calc(session: requests.Session, body: dict, fast: bool = True) -> dict:
    endpoint = "/estimator/calculate-fast" if fast else "/estimator/calculate"
    r = session.post(BASE_URL + endpoint, json=body, timeout=60)
    r.raise_for_status()
    return r.json()


def total(result: dict) -> float:
    return float(result["totals"]["total_project_cost"])


def util_total(result: dict) -> float:
    return float(result.get("utilities_total", 0))


def main() -> int:
    s = requests.Session()
    report = {
        "base_url": BASE_URL,
        "rate_index": None,
        "full_calculate_live_index": None,
        "baseline": None,
        "one_off_patch_tests": [],
        "utility_scope_tests": [],
        "regression_tests": [],
        "display_only_tests": [],
        "failures": [],
    }

    rate = s.get(BASE_URL + "/estimator/rate-index", timeout=30)
    rate.raise_for_status()
    report["rate_index"] = rate.json()
    for k in ["source", "copper_usd_oz", "material_index", "delta_pct", "fetched_at"]:
        if k not in report["rate_index"]:
            report["failures"].append(f"rate-index missing {k}")

    full = post_calc(s, DEFAULT_BODY, fast=False)
    report["full_calculate_live_index"] = {
        "source": full.get("live_rate_index", {}).get("source"),
        "live_rate_index_material_index": full.get("live_rate_index", {}).get("material_index"),
        "multipliers_live_material_index": full.get("multipliers", {}).get("live_material_index"),
        "total_project_cost": total(full),
    }
    if full.get("live_rate_index", {}).get("material_index") != full.get("multipliers", {}).get("live_material_index"):
        report["failures"].append("calculate does not apply returned live_rate_index.material_index to multipliers.live_material_index")

    baseline = post_calc(s, DEFAULT_BODY, fast=True)
    baseline_total = total(baseline)
    baseline_utils = util_total(baseline)
    report["baseline"] = {
        "total_project_cost": baseline_total,
        "utilities_total": baseline_utils,
        "multipliers": baseline.get("multipliers"),
        "live_rate_index": baseline.get("live_rate_index"),
    }

    required_patches = [
        {"industry_type": "Warehouse / Logistics"},
        {"industry_type": "Process Building"},
        {"continent": "North America"},
        {"continent": "Africa"},
        {"bay_spacing_m": 4},
        {"soil_type": "Clayey"},
        {"wind_speed_ms": 40},
        {"annual_output_mt": 80000},
        {"tempering_utility_demand": "Very High"},
        {"chocolate_storage_temp_c": 8},
        {"process_hot_water_lph": 10000},
        {"dust_collection_required": False, "product_category": "Biscuit Plant"},
        {"cooling_conveyor_load": "Heavy Duty", "product_category": "Biscuit Plant"},
        {"land_area_sqm": 80000},
        {"far_fsi": 2.5},
        {"relative_humidity_pct": 90},
    ]
    # For biscuit-specific field patches, compare against a Biscuit Plant baseline so the tested field itself must create the delta.
    biscuit_base = post_calc(s, patch_body({"product_category": "Biscuit Plant"}), fast=True)
    for p in required_patches:
        compare = biscuit_base if p.get("product_category") == "Biscuit Plant" else baseline
        res = post_calc(s, patch_body(p), fast=True)
        delta = total(res) - total(compare)
        ok = abs(delta) >= 1.0
        item = {"patch": p, "compare_total": total(compare), "variant_total": total(res), "delta": round(delta, 2), "passed": ok}
        report["one_off_patch_tests"].append(item)
        if not ok:
            report["failures"].append(f"one-off patch did not change total by >= $1: {p}; delta={delta}")

    reduced_scope = post_calc(s, patch_body({"utility_scope": ["Water Treatment Plant", "Fire Fighting System", "Electrical Substation"]}), fast=True)
    empty_scope = post_calc(s, patch_body({"utility_scope": []}), fast=True)
    scope_tests = [
        {
            "name": "reduced utility scope lowers utilities_total",
            "baseline_utilities_total": baseline_utils,
            "variant_utilities_total": util_total(reduced_scope),
            "baseline_total": baseline_total,
            "variant_total": total(reduced_scope),
            "passed": util_total(reduced_scope) < baseline_utils,
        },
        {
            "name": "empty utility scope utilities_total is zero",
            "variant_utilities_total": util_total(empty_scope),
            "variant_total": total(empty_scope),
            "passed": util_total(empty_scope) == 0,
        },
    ]
    report["utility_scope_tests"] = scope_tests
    for t in scope_tests:
        if not t["passed"]:
            report["failures"].append(f"utility_scope failed: {t['name']}")

    regression_defs = [
        ("project_type Retrofit lowers total", {"project_type": "Retrofit / Capacity Upgrade"}, lambda r: total(r) < baseline_total),
        ("foundation_type Pile raises total", {"foundation_type": "Pile Foundation"}, lambda r: total(r) > baseline_total),
        ("region India/South Asia lowers total", {"region": "India / South Asia"}, lambda r: total(r) < baseline_total),
        ("location_tier Remote raises total", {"location_tier": "Remote"}, lambda r: total(r) > baseline_total),
        ("contingency_pct changes contingency line", {"contingency_pct": 20.0}, lambda r: float(r["totals"]["contingency"]) != float(baseline["totals"]["contingency"]) and total(r) > baseline_total),
    ]
    for name, p, predicate in regression_defs:
        res = post_calc(s, patch_body(p), fast=True)
        ok = predicate(res)
        item = {"name": name, "patch": p, "baseline_total": baseline_total, "variant_total": total(res), "passed": ok}
        if "contingency" in name:
            item.update({"baseline_contingency": baseline["totals"]["contingency"], "variant_contingency": res["totals"]["contingency"]})
        report["regression_tests"].append(item)
        if not ok:
            report["failures"].append(f"regression failed: {name}")

    cx_base_body = patch_body({"complexity": {k: False for k in DEFAULT_BODY["complexity"]}})
    cx_base = post_calc(s, cx_base_body, fast=True)
    for key in DEFAULT_BODY["complexity"]:
        body = deepcopy(cx_base_body)
        body["complexity"][key] = True
        res = post_calc(s, body, fast=True)
        ok = total(res) != total(cx_base)
        item = {"name": f"complexity.{key} changes total", "baseline_total": total(cx_base), "variant_total": total(res), "passed": ok}
        report["regression_tests"].append(item)
        if not ok:
            report["failures"].append(f"regression failed: complexity.{key} did not change total")

    for p in [{"currency": "EUR"}, {"base_unit": "ft"}, {"currency": "INR", "base_unit": "m"}]:
        res = post_calc(s, patch_body(p), fast=True)
        delta = total(res) - baseline_total
        ok = abs(delta) < 0.01
        item = {"patch": p, "baseline_total_usd": baseline_total, "variant_total_project_cost_usd": total(res), "delta": round(delta, 4), "passed": ok}
        report["display_only_tests"].append(item)
        if not ok:
            report["failures"].append(f"display-only control changed USD total_project_cost: {p}; delta={delta}")

    out = Path("/app/test_reports/estimator_api_iteration3_results.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())