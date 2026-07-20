#!/usr/bin/env python3
"""Iteration 4 focused backend verification for estimator live API costs and field-impact bug.

User bug: estimator total must update when editable elements change and must be calculated using live API costs.
"""
import json
import math
import os
import sys
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
RESULT_PATH = Path("/app/test_reports/estimator_live_api_iteration4_results.json")

DEFAULT_BODY = {
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


def patch_body(patch: dict) -> dict:
    body = deepcopy(DEFAULT_BODY)
    body.update(patch)
    return body


def total(result: dict) -> float:
    return float(result["totals"]["total_project_cost"])


def util_total(result: dict) -> float:
    return float(result.get("utilities_total", 0))


def post_calc(session: requests.Session, body: dict, fast: bool = True) -> dict:
    endpoint = "/estimator/calculate-fast" if fast else "/estimator/calculate"
    r = session.post(BASE_URL + endpoint, json=body, timeout=90)
    r.raise_for_status()
    return r.json()


def write_report(report: dict) -> None:
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(report, indent=2))


def main() -> int:
    s = requests.Session()
    report = {
        "base_url": BASE_URL,
        "external_hg": None,
        "rate_index": None,
        "calculate": None,
        "calculate_fast": None,
        "local_static_baseline": None,
        "live_scaling_check": None,
        "field_impact_tests": [],
        "utility_scope_tests": [],
        "failures": [],
    }

    try:
        ext = s.get("https://api.gold-api.com/price/HG", timeout=30)
        try:
            ext_json = ext.json()
        except Exception:
            ext_json = {"raw": ext.text[:500]}
        report["external_hg"] = {"status_code": ext.status_code, "json": ext_json}
        price = ext_json.get("price") if isinstance(ext_json, dict) else None
        if ext.status_code != 200 or not isinstance(price, (int, float)) or float(price) <= 0:
            report["failures"].append(f"direct HG price endpoint did not return HTTP 200 with positive numeric price: {report['external_hg']}")
    except Exception as e:
        report["external_hg"] = {"error": repr(e)}
        report["failures"].append(f"direct HG price endpoint request failed: {e!r}")

    try:
        rate_resp = s.get(BASE_URL + "/estimator/rate-index", timeout=30)
        rate_resp.raise_for_status()
        rate = rate_resp.json()
        report["rate_index"] = rate
        if rate.get("source") != "api.gold-api.com":
            report["failures"].append(f"rate-index source expected api.gold-api.com, got {rate.get('source')!r}")
        if rate.get("commodity") != "copper":
            report["failures"].append(f"rate-index commodity expected copper, got {rate.get('commodity')!r}")
        if rate.get("price_unit") != "USD/lb":
            report["failures"].append(f"rate-index price_unit expected USD/lb, got {rate.get('price_unit')!r}")
        if not isinstance(rate.get("price"), (int, float)) or float(rate.get("price") or 0) <= 0:
            report["failures"].append(f"rate-index price is not positive numeric: {rate.get('price')!r}")
        if math.isclose(float(rate.get("material_index", 1.0)), 1.0, abs_tol=1e-9):
            report["failures"].append(f"rate-index material_index should not be 1.0, got {rate.get('material_index')!r}")
        if math.isclose(float(rate.get("delta_pct", 0.0)), 0.0, abs_tol=1e-9):
            report["failures"].append(f"rate-index delta_pct should not be 0, got {rate.get('delta_pct')!r}")
    except Exception as e:
        report["failures"].append(f"/estimator/rate-index failed: {e!r}")
        write_report(report)
        return 1

    try:
        full = post_calc(s, DEFAULT_BODY, fast=False)
        fast = post_calc(s, DEFAULT_BODY, fast=True)
        report["calculate"] = {
            "total_project_cost": total(full),
            "utilities_total": util_total(full),
            "live_rate_index": full.get("live_rate_index"),
            "multipliers": full.get("multipliers"),
        }
        report["calculate_fast"] = {
            "total_project_cost": total(fast),
            "utilities_total": util_total(fast),
            "live_rate_index": fast.get("live_rate_index"),
            "multipliers": fast.get("multipliers"),
        }
        api_index = float(report["rate_index"].get("material_index"))
        for label, result in [("calculate", full), ("calculate-fast", fast)]:
            mult_index = float(result.get("multipliers", {}).get("live_material_index", -1))
            result_index = float(result.get("live_rate_index", {}).get("material_index", -1))
            if not math.isclose(mult_index, api_index, rel_tol=0, abs_tol=0.0001):
                report["failures"].append(f"{label} multipliers.live_material_index {mult_index} != rate-index material_index {api_index}")
            if not math.isclose(result_index, api_index, rel_tol=0, abs_tol=0.0001):
                report["failures"].append(f"{label} live_rate_index.material_index {result_index} != rate-index material_index {api_index}")

        # Compare API live total against local computation with the same model but static material_index=1.0.
        sys.path.insert(0, "/app/backend")
        from server import ProjectInputs, compute_estimate  # noqa: E402

        static = compute_estimate(ProjectInputs(**DEFAULT_BODY), live_index={"source": "test", "material_index": 1.0})
        static_total = total(static)
        expected_live_total = round(static_total * api_index, 2)
        api_total = total(full)
        report["local_static_baseline"] = {"total_project_cost": static_total, "multipliers": static.get("multipliers")}
        report["live_scaling_check"] = {
            "static_total": static_total,
            "live_index": api_index,
            "expected_live_total_static_x_index": expected_live_total,
            "api_calculate_total": api_total,
            "absolute_delta": round(api_total - expected_live_total, 2),
            "passed": math.isclose(api_total, expected_live_total, rel_tol=0.003, abs_tol=5000),
        }
        if not report["live_scaling_check"]["passed"]:
            report["failures"].append(f"calculate total {api_total} does not match static baseline {static_total} * live index {api_index} ~= {expected_live_total}")
    except Exception as e:
        report["failures"].append(f"calculate/live-scaling checks failed: {e!r}")
        write_report(report)
        return 1

    baseline_result = post_calc(s, DEFAULT_BODY, fast=True)
    baseline_total = total(baseline_result)
    baseline_utils = util_total(baseline_result)
    biscuit_base = post_calc(s, patch_body({"product_category": "Biscuit Plant"}), fast=True)

    field_patches = [
        {"name": "industry_type Warehouse lowers total", "patch": {"industry_type": "Warehouse / Logistics"}, "compare": "baseline", "predicate": lambda d, vt, ct, vu, cu: vt < ct},
        {"name": "industry_type Process changes total", "patch": {"industry_type": "Process Building"}, "compare": "baseline", "predicate": lambda d, vt, ct, vu, cu: abs(d) >= 1},
        {"name": "continent North America changes total", "patch": {"continent": "North America"}, "compare": "baseline", "predicate": lambda d, vt, ct, vu, cu: abs(d) >= 1},
        {"name": "continent Africa lowers total", "patch": {"continent": "Africa"}, "compare": "baseline", "predicate": lambda d, vt, ct, vu, cu: vt < ct},
        {"name": "bay_spacing_m changes total", "patch": {"bay_spacing_m": 4}, "compare": "baseline", "predicate": lambda d, vt, ct, vu, cu: abs(d) >= 1},
        {"name": "soil_type changes total", "patch": {"soil_type": "Clayey"}, "compare": "baseline", "predicate": lambda d, vt, ct, vu, cu: abs(d) >= 1},
        {"name": "wind_speed_ms changes total", "patch": {"wind_speed_ms": 40}, "compare": "baseline", "predicate": lambda d, vt, ct, vu, cu: abs(d) >= 1},
        {"name": "annual_output_mt changes utilities_total", "patch": {"annual_output_mt": 80000}, "compare": "baseline", "predicate": lambda d, vt, ct, vu, cu: abs(vu - cu) >= 1},
        {"name": "tempering_utility_demand changes utilities_total", "patch": {"tempering_utility_demand": "Very High"}, "compare": "baseline", "predicate": lambda d, vt, ct, vu, cu: abs(vu - cu) >= 1},
        {"name": "chocolate_storage_temp_c changes utilities_total", "patch": {"chocolate_storage_temp_c": 8}, "compare": "baseline", "predicate": lambda d, vt, ct, vu, cu: abs(vu - cu) >= 1},
        {"name": "process_hot_water_lph changes utilities_total", "patch": {"process_hot_water_lph": 10000}, "compare": "baseline", "predicate": lambda d, vt, ct, vu, cu: abs(vu - cu) >= 1},
        {"name": "dust_collection_required changes biscuit utilities_total", "patch": {"dust_collection_required": False, "product_category": "Biscuit Plant"}, "compare": "biscuit", "predicate": lambda d, vt, ct, vu, cu: abs(vu - cu) >= 1},
        {"name": "cooling_conveyor_load changes biscuit utilities_total", "patch": {"cooling_conveyor_load": "Heavy Duty", "product_category": "Biscuit Plant"}, "compare": "biscuit", "predicate": lambda d, vt, ct, vu, cu: abs(vu - cu) >= 1},
        {"name": "land_area_sqm changes total", "patch": {"land_area_sqm": 80000}, "compare": "baseline", "predicate": lambda d, vt, ct, vu, cu: abs(d) >= 1},
        {"name": "far_fsi changes total", "patch": {"far_fsi": 2.5}, "compare": "baseline", "predicate": lambda d, vt, ct, vu, cu: abs(d) >= 1},
        {"name": "relative_humidity_pct changes utilities_total", "patch": {"relative_humidity_pct": 90}, "compare": "baseline", "predicate": lambda d, vt, ct, vu, cu: abs(vu - cu) >= 1},
    ]
    for t in field_patches:
        compare_result = biscuit_base if t["compare"] == "biscuit" else baseline_result
        variant = post_calc(s, patch_body(t["patch"]), fast=True)
        ct = total(compare_result)
        vt = total(variant)
        cu = util_total(compare_result)
        vu = util_total(variant)
        delta = vt - ct
        passed = bool(t["predicate"](delta, vt, ct, vu, cu))
        item = {
            "name": t["name"],
            "patch": t["patch"],
            "compare_total": ct,
            "variant_total": vt,
            "delta_total": round(delta, 2),
            "compare_utilities_total": cu,
            "variant_utilities_total": vu,
            "delta_utilities_total": round(vu - cu, 2),
            "passed": passed,
        }
        report["field_impact_tests"].append(item)
        if not passed:
            report["failures"].append(f"field-impact failed: {t['name']} patch={t['patch']} delta_total={delta} delta_utilities={vu - cu}")

    reduced_scope = post_calc(s, patch_body({"utility_scope": ["Water Treatment Plant", "Fire Fighting System", "Electrical Substation"]}), fast=True)
    empty_scope = post_calc(s, patch_body({"utility_scope": []}), fast=True)
    utility_tests = [
        {
            "name": "reduced utility_scope lowers utilities_total",
            "baseline_utilities_total": baseline_utils,
            "variant_utilities_total": util_total(reduced_scope),
            "baseline_total": baseline_total,
            "variant_total": total(reduced_scope),
            "passed": util_total(reduced_scope) < baseline_utils and total(reduced_scope) < baseline_total,
        },
        {
            "name": "empty utility_scope has zero utilities_total",
            "baseline_utilities_total": baseline_utils,
            "variant_utilities_total": util_total(empty_scope),
            "baseline_total": baseline_total,
            "variant_total": total(empty_scope),
            "passed": util_total(empty_scope) == 0 and total(empty_scope) < baseline_total,
        },
    ]
    report["utility_scope_tests"] = utility_tests
    for t in utility_tests:
        if not t["passed"]:
            report["failures"].append(f"utility_scope failed: {t['name']}")

    write_report(report)
    print(json.dumps(report, indent=2))
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())