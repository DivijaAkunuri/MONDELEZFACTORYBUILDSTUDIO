#!/usr/bin/env python3
"""Focused backend verification for city-specific estimator cost factors."""

import json
import math
import os
from pathlib import Path

import requests


def frontend_backend_url() -> str:
    env_path = Path("/app/frontend/.env")
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("REACT_APP_BACKEND_URL="):
                return line.split("=", 1)[1].strip().strip('"')
    return os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001")


BASE = frontend_backend_url().rstrip("/") + "/api"


def payload(city, country="India", region="India / South Asia", continent="Asia", **overrides):
    p = {
        "project_name": "City Factor Verification Plant",
        "project_type": "Greenfield",
        "industry_type": "Food",
        "product_category": "Chocolate Plant",
        "location_city": city,
        "location_country": country,
        "region": region,
        "continent": continent,
        "location_tier": "Metro",
        "utility_scope": [
            "Boiler House",
            "Chiller Plant",
            "HVAC System",
            "Air Compressors",
            "Water Treatment Plant",
            "Fire Fighting System",
            "Electrical Substation",
        ],
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
    }
    p.update(overrides)
    return p


def calc(city, country="India", region="India / South Asia", continent="Asia", **overrides):
    r = requests.post(
        f"{BASE}/estimator/calculate-fast",
        json=payload(city, country, region, continent, **overrides),
        timeout=45,
    )
    r.raise_for_status()
    return r.json()


def total(result):
    return result["totals"]["total_project_cost"]


def boq_rate(result, activity="Excavation"):
    row = next(r for r in result["boq"] if r.get("activity") == activity)
    return row["rate"]


def approx_equal(a, b, eps=0.01):
    return abs(float(a) - float(b)) <= eps


def require(cond, msg, failures):
    if not cond:
        failures.append(msg)


def main():
    failures = []
    evidence = {"base_url": BASE, "india_totals": {}, "pair_totals": {}}

    # Reference endpoint must expose known cities.
    ref = requests.get(f"{BASE}/estimator/reference", timeout=30)
    ref.raise_for_status()
    ref_json = ref.json()
    cities = ref_json.get("cities")
    require(isinstance(cities, list) and len(cities) >= 50, "reference.cities missing or unexpectedly small", failures)
    for city in ["Mumbai", "Nagpur", "Delhi", "Bangalore", "Hamburg", "New York", "Singapore"]:
        require(city in cities, f"reference.cities missing {city}", failures)
    evidence["reference_city_count"] = len(cities or [])

    # India city totals must no longer be constant.
    india_cities = [
        "Mumbai", "Delhi", "Bangalore", "Chennai", "Hyderabad", "Pune",
        "Kolkata", "Ahmedabad", "Nagpur", "Indore", "Coimbatore", "Chandigarh",
    ]
    results = {c: calc(c) for c in india_cities}
    totals = {c: total(r) for c, r in results.items()}
    evidence["india_totals"] = totals
    rounded_totals = [round(v, 2) for v in totals.values()]
    require(len(set(rounded_totals)) == len(india_cities), f"India city totals not all unique: {totals}", failures)
    require(totals["Mumbai"] > totals["Delhi"] > totals["Bangalore"], "Expected Mumbai > Delhi > Bangalore", failures)
    require(totals["Bangalore"] > totals["Kolkata"], "Expected Bangalore > Kolkata", failures)
    require(totals["Chandigarh"] > totals["Coimbatore"] > totals["Nagpur"], "Expected Chandigarh > Coimbatore > Nagpur", failures)

    # City factors schema for known city.
    mumbai_cf = results["Mumbai"].get("city_factors")
    required_keys = {
        "matched", "resolved", "requested", "civil", "mechanical", "electrical", "labour",
        "civil_effective", "mechanical_effective", "electrical_effective",
    }
    require(isinstance(mumbai_cf, dict), "city_factors missing for Mumbai", failures)
    if isinstance(mumbai_cf, dict):
        require(required_keys.issubset(mumbai_cf), f"city_factors missing keys: {required_keys - set(mumbai_cf)}", failures)
        require(mumbai_cf.get("matched") is True and mumbai_cf.get("resolved") == "Mumbai", f"Mumbai not matched/resolved correctly: {mumbai_cf}", failures)
        require(mumbai_cf.get("requested") == "Mumbai", f"Mumbai requested not echoed: {mumbai_cf}", failures)
    evidence["mumbai_city_factors"] = mumbai_cf

    # Unknown city must be neutral fallback.
    unknown = calc("Random Town")
    unknown_cf = unknown.get("city_factors")
    require(unknown_cf and unknown_cf.get("matched") is False and unknown_cf.get("resolved") is None, f"Unknown city not unmatched: {unknown_cf}", failures)
    if unknown_cf:
        for k in ["civil", "mechanical", "electrical", "labour", "civil_effective", "mechanical_effective", "electrical_effective"]:
            require(approx_equal(unknown_cf.get(k), 1.0), f"Unknown city factor {k} not 1.0: {unknown_cf}", failures)
        require(unknown_cf.get("requested") == "Random Town", f"Unknown requested city not echoed: {unknown_cf}", failures)
    evidence["unknown_city_factors"] = unknown_cf

    # Civil BOQ rates must change city-to-city.
    mum_rate = boq_rate(results["Mumbai"], "Excavation")
    nag_rate = boq_rate(results["Nagpur"], "Excavation")
    require(not approx_equal(mum_rate, nag_rate), f"Civil BOQ Excavation rate did not change Mumbai vs Nagpur: {mum_rate} vs {nag_rate}", failures)
    evidence["boq_excavation_rates"] = {"Mumbai": mum_rate, "Nagpur": nag_rate}

    # Utilities must carry and respect discipline.
    utilities = results["Mumbai"].get("utilities") or []
    disciplines_by_name = {u.get("name"): u.get("discipline") for u in utilities}
    expected_disc = {
        "Water Supply System": "civil",
        "Steam & Boiler System": "mechanical",
        "Refrigeration / Cold Chain": "mechanical",
        "Compressed Air System": "mechanical",
        "Electrical Infrastructure": "electrical",
        "Fire Fighting System": "mechanical",
    }
    for name, disc in expected_disc.items():
        require(disciplines_by_name.get(name) == disc, f"Utility {name} discipline expected {disc}, got {disciplines_by_name.get(name)}", failures)
    evidence["utility_disciplines_mumbai"] = disciplines_by_name

    etp_only = calc("Mumbai", utility_scope=["ETP / STP System", "Water Supply System"])
    etp_disciplines = {u.get("name"): u.get("discipline") for u in etp_only.get("utilities", [])}
    require(etp_disciplines.get("ETP / STP System") == "civil", f"ETP / STP discipline expected civil, got {etp_disciplines}", failures)
    require(etp_disciplines.get("Water Supply System") == "civil", f"Water Supply discipline expected civil in scoped call, got {etp_disciplines}", failures)
    evidence["utility_disciplines_etp_scope"] = etp_disciplines

    cairo = calc("Cairo", country="Egypt", region="Africa", continent="Africa")
    africa_neutral = calc("Random Town", country="Egypt", region="Africa", continent="Africa")
    cairo_amounts = {u["name"]: u["amount"] for u in cairo.get("utilities", [])}
    neutral_amounts = {u["name"]: u["amount"] for u in africa_neutral.get("utilities", [])}
    cairo_ratios = {name: round(cairo_amounts[name] / neutral_amounts[name], 4) for name in cairo_amounts if name in neutral_amounts and neutral_amounts[name]}
    # Cairo's effective civil factor is lower than mechanical/electrical; civil utilities should drop more than mech/elec.
    require(cairo_ratios.get("Steam & Boiler System", 0) > cairo_ratios.get("Water Supply System", 1), f"Mechanical utility did not differ as expected from civil for Cairo: {cairo_ratios}", failures)
    require(cairo_ratios.get("Electrical Infrastructure", 0) > cairo_ratios.get("Water Supply System", 1), f"Electrical utility did not differ as expected from civil for Cairo: {cairo_ratios}", failures)
    evidence["cairo_vs_neutral_utility_ratios"] = cairo_ratios

    # Similar city shifts outside India.
    pairs = [
        ("Hamburg", "Munich", "Germany", "Europe", "Europe"),
        ("New York", "Houston", "USA", "North America", "North America"),
        ("Dubai", "Riyadh", "UAE", "Middle East", "Asia"),
        ("Bangkok", "Singapore", "Thailand", "ASEAN", "Asia"),
    ]
    for a, b, country, region, continent in pairs:
        ra = calc(a, country=country, region=region, continent=continent)
        rb = calc(b, country=country, region=region, continent=continent)
        evidence["pair_totals"][f"{a} vs {b}"] = {a: total(ra), b: total(rb)}
        require(total(ra) != total(rb), f"Pair totals identical for {a} vs {b}", failures)
        require(ra.get("city_factors", {}).get("matched") is True, f"{a} not city-factor matched", failures)
        require(rb.get("city_factors", {}).get("matched") is True, f"{b} not city-factor matched", failures)

    # Small regression checks related to recalc sensitivity: confidence responds to project type/complexity.
    green = calc("Mumbai")
    retrofit = calc("Mumbai", project_type="Retrofit / Capacity Upgrade")
    complex_remote = calc("Mumbai", complexity={
        "seismic_zone_high": False,
        "high_humidity": False,
        "cold_region": False,
        "brownfield": True,
        "gmp_hygienic": True,
        "explosion_risk": True,
        "utility_redundancy": True,
        "high_floor_load": False,
        "remote_site": True,
    })
    evidence["confidence"] = {
        "greenfield": green["totals"]["confidence_score"],
        "retrofit": retrofit["totals"]["confidence_score"],
        "complex_remote": complex_remote["totals"]["confidence_score"],
    }
    require(retrofit["totals"]["confidence_score"] < green["totals"]["confidence_score"], "Confidence did not decrease for retrofit", failures)
    require(complex_remote["totals"]["confidence_score"] < green["totals"]["confidence_score"], "Confidence did not decrease for added complexity", failures)

    print(json.dumps({"failures": failures, "evidence": evidence}, indent=2, sort_keys=True))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())