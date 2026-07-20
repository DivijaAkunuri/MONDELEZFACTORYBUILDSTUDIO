#!/usr/bin/env python3
"""Focused API verification for estimator recalculation/live-rate bug."""
import json
import os
import sys
from copy import deepcopy
from pathlib import Path

import requests


def read_frontend_backend_url() -> str:
    env_path = Path("/app/frontend/.env")
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("REACT_APP_BACKEND_URL="):
                return line.split("=", 1)[1].strip().strip('"')
    return os.environ.get("REACT_APP_BACKEND_URL", "https://predict-calc-1.preview.emergentagent.com")


BASE_URL = read_frontend_backend_url().rstrip("/") + "/api"

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


def post_calc(session: requests.Session, inputs: dict, fast: bool = True) -> dict:
    endpoint = "/estimator/calculate-fast" if fast else "/estimator/calculate"
    r = session.post(BASE_URL + endpoint, json=inputs, timeout=45)
    r.raise_for_status()
    return r.json()


def money(result: dict) -> float:
    return float(result["totals"]["total_project_cost"])


def variant(**changes) -> dict:
    d = deepcopy(DEFAULT_INPUTS)
    for k, v in changes.items():
        d[k] = v
    return d


def run():
    session = requests.Session()
    report = {"base_url": BASE_URL, "rate_index": None, "live_calculate": None, "directional_tests": [], "non_effect_editable_tests": [], "failures": []}

    # Live rate endpoint contract.
    rr = session.get(BASE_URL + "/estimator/rate-index", timeout=20)
    rr.raise_for_status()
    rate_index = rr.json()
    report["rate_index"] = rate_index
    required = ["source", "copper_usd_oz", "material_index", "delta_pct", "fetched_at"]
    missing = [k for k in required if k not in rate_index]
    if missing:
        report["failures"].append(f"rate-index missing keys: {missing}")
    if rate_index.get("source") == "fallback" and rate_index.get("material_index") != 1.0:
        report["failures"].append("fallback rate-index did not return material_index=1.0")

    # calculate (non-fast) must reflect the live material index in multipliers.
    calc_full = post_calc(session, DEFAULT_INPUTS, fast=False)
    report["live_calculate"] = {
        "source": calc_full.get("live_rate_index", {}).get("source"),
        "live_rate_index_material_index": calc_full.get("live_rate_index", {}).get("material_index"),
        "multipliers_live_material_index": calc_full.get("multipliers", {}).get("live_material_index"),
        "total_project_cost": money(calc_full),
    }
    if calc_full.get("live_rate_index", {}).get("material_index") != calc_full.get("multipliers", {}).get("live_material_index"):
        report["failures"].append("calculate response live_rate_index.material_index does not match multipliers.live_material_index")

    base = post_calc(session, DEFAULT_INPUTS, fast=True)
    base_total = money(base)
    base_utilities = float(base.get("utilities_total", 0))
    report["baseline_fast"] = {"total_project_cost": base_total, "utilities_total": base_utilities, "multipliers": base.get("multipliers")}

    checks = [
        ("project_type", variant(project_type="Retrofit / Capacity Upgrade"), "lt", "Retrofit should lower total vs Greenfield"),
        ("region", variant(region="India / South Asia"), "lt", "India / South Asia should lower total vs Europe"),
        ("location_tier", variant(location_tier="Remote"), "gt", "Remote should raise total vs Metro"),
        ("foundation_type", variant(foundation_type="Pile Foundation"), "gt", "Pile Foundation should raise total vs Raft"),
        ("soil_hardness", variant(soil_hardness="Soft"), "gt", "Soft soil should raise total vs Medium"),
        ("sbc_soil_type", variant(sbc_soil_type="Black Cotton"), "gt", "Black Cotton should raise total vs Hard Stone"),
        ("gwt_depth", variant(gwt_depth="Shallow (<3 m)"), "gt", "Shallow GWT should raise total vs Medium"),
        ("wind_zone", variant(wind_zone="Zone 5 (Cyclonic)"), "gt", "Zone 5 should raise total vs Zone 2"),
        ("seismic_zone", variant(seismic_zone="Zone V (High)"), "gt", "Zone V should raise total vs Zone 0"),
        ("roof_type", variant(roof_type="RCC Slab"), "gt", "RCC slab should raise total vs PEB"),
        ("column_type", variant(column_type="RCC"), "gt", "RCC columns should raise total vs Steel"),
        ("fuel_type", variant(fuel_type="Electric"), "gt", "Electric fuel should raise utility cost vs PNG"),
        ("grid_reliability", variant(grid_reliability="Poor (frequent outages)"), "gt", "Poor grid should raise total vs Good"),
        ("water_availability", variant(water_availability="Limited"), "gt", "Limited water should raise total vs Municipal+Borewell"),
        ("ambient_temp_range", variant(ambient_temp_range="Tropical (25°C - 40°C)"), "gt", "Tropical should raise total vs Temperate"),
        ("building_type", variant(building_type="Warehouse"), "lt", "Warehouse should lower total vs RCC+PEB"),
        ("production_capacity_tpd", variant(production_capacity_tpd=240), "gt", "240 TPD should raise total vs 120 TPD"),
        ("utility_scope_remove", variant(utility_scope=["Water Treatment Plant", "Fire Fighting System", "Electrical Substation"]), "util_lt", "Removing utilities should lower utilities_total"),
        ("contingency_pct", variant(contingency_pct=20.0), "gt", "Higher contingency should raise total"),
    ]
    for name, payload, op, note in checks:
        res = post_calc(session, payload, fast=True)
        total = money(res)
        utilities = float(res.get("utilities_total", 0))
        if op == "gt":
            ok = total > base_total
        elif op == "lt":
            ok = total < base_total
        elif op == "util_lt":
            ok = utilities < base_utilities and total != base_total
        else:
            ok = False
        item = {"field": name, "baseline_total": base_total, "variant_total": total, "baseline_utilities": base_utilities, "variant_utilities": utilities, "passed": ok, "expectation": note}
        report["directional_tests"].append(item)
        if not ok:
            report["failures"].append(f"directional check failed for {name}: {note}; got total {total}, utilities {utilities}")

    # GWT exact direction Deep vs Shallow from requested text.
    deep = post_calc(session, variant(gwt_depth="Deep (>8 m)"), fast=True)
    shallow = post_calc(session, variant(gwt_depth="Shallow (<3 m)"), fast=True)
    gwt_ok = money(shallow) > money(deep)
    report["directional_tests"].append({"field": "gwt_depth_deep_vs_shallow", "deep_total": money(deep), "shallow_total": money(shallow), "passed": gwt_ok})
    if not gwt_ok:
        report["failures"].append("GWT Shallow did not cost more than Deep")

    # Grid/water exact lower-cost baselines from requested text.
    excellent = post_calc(session, variant(grid_reliability="Excellent"), fast=True)
    poor = post_calc(session, variant(grid_reliability="Poor (frequent outages)"), fast=True)
    grid_ok = money(poor) > money(excellent)
    report["directional_tests"].append({"field": "grid_excellent_vs_poor", "excellent_total": money(excellent), "poor_total": money(poor), "passed": grid_ok})
    if not grid_ok:
        report["failures"].append("Poor grid did not cost more than Excellent grid")
    municipal = post_calc(session, variant(water_availability="Municipal"), fast=True)
    limited = post_calc(session, variant(water_availability="Limited"), fast=True)
    water_ok = money(limited) > money(municipal)
    report["directional_tests"].append({"field": "water_municipal_vs_limited", "municipal_total": money(municipal), "limited_total": money(limited), "passed": water_ok})
    if not water_ok:
        report["failures"].append("Limited water did not cost more than Municipal")

    # Each complexity toggle should change the total/multiplier.
    all_false_complexity = {k: False for k in DEFAULT_INPUTS["complexity"]}
    cx_base_inputs = variant(complexity=all_false_complexity)
    cx_base = post_calc(session, cx_base_inputs, fast=True)
    cx_base_total = money(cx_base)
    for key in DEFAULT_INPUTS["complexity"]:
        cx = deepcopy(cx_base_inputs)
        cx["complexity"][key] = True
        res = post_calc(session, cx, fast=True)
        ok = money(res) != cx_base_total and res.get("multipliers", {}).get("complexity") != cx_base.get("multipliers", {}).get("complexity")
        item = {"field": f"complexity.{key}", "baseline_total": cx_base_total, "variant_total": money(res), "baseline_complexity_m": cx_base.get("multipliers", {}).get("complexity"), "variant_complexity_m": res.get("multipliers", {}).get("complexity"), "passed": ok}
        report["directional_tests"].append(item)
        if not ok:
            report["failures"].append(f"complexity toggle {key} did not change total and complexity multiplier")

    # Contract edge: editable fields that still do not alter total_project_cost.
    non_effect_candidates = [
        ("industry_type", "FMCG"),
        ("continent", "Asia"),
        ("bay_spacing_m", 12),
        ("soil_type", "Black Cotton"),
        ("wind_speed_ms", 42),
        ("annual_output_mt", 72000),
        ("tempering_utility_demand", "Very High"),
        ("chocolate_storage_temp_c", 10),
        ("process_hot_water_lph", 5000),
        ("dust_collection_required", False),
        ("cooling_conveyor_load", "Heavy Duty"),
        ("land_area_sqm", 64000),
        ("far_fsi", 2.4),
        ("relative_humidity_pct", 95),
        ("currency", "EUR"),
        ("base_unit", "ft"),
    ]
    for field, value in non_effect_candidates:
        payload = variant(**{field: value})
        # Biscuit-only fields need biscuit product to be semantically active/visible.
        if field in {"dust_collection_required", "cooling_conveyor_load"}:
            payload["product_category"] = "Biscuit Plant"
            base_payload = variant(product_category="Biscuit Plant")
            field_base = post_calc(session, base_payload, fast=True)
            field_base_total = money(field_base)
        else:
            field_base_total = base_total
        res = post_calc(session, payload, fast=True)
        changed = money(res) != field_base_total
        item = {"field": field, "changed_to": value, "baseline_total": field_base_total, "variant_total": money(res), "changes_total_project_cost": changed}
        report["non_effect_editable_tests"].append(item)
        if not changed:
            report["failures"].append(f"editable field {field} did not change total_project_cost")

    out = Path("/app/test_reports/estimator_api_results.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    sys.exit(run())