from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import json
import re
import uuid
import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict
import httpx

from rate_data import (
    CIVIL_ACTIVITIES, UTILITY_SYSTEMS, REGION_MULTIPLIERS,
    LOCATION_FACTOR, COMPLEXITY_FACTORS, INDUSTRY_PRESETS,
    COMPLIANCE_ADDER_PCT, CONTINGENCY_PCT, CURRENCY_SYMBOLS,
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

# ---------- Models ----------
class ProjectInputs(BaseModel):
    model_config = ConfigDict(extra="allow")
    # Step 1 - Project Identification
    project_name: str = "Chocolate & Bakery Manufacturing Plant"
    project_type: str = "Greenfield"           # Greenfield / Brownfield / Retrofit
    industry_type: str = "Food"                 # Food / FMCG / Warehouse / Process Building
    product_category: str = "Chocolate Plant"   # Chocolate Plant / Biscuit Plant / ...
    location_city: str = "Hamburg"
    location_country: str = "Germany"
    region: str = "Europe"                      # Stage 2 region
    continent: str = "Europe"                   # Stage 3 world/continent
    location_tier: str = "Metro"                # Metro / Non-Metro / Remote
    # Step 2 - geometry
    building_type: str = "Industrial Building (RCC + PEB)"
    length_m: float = 185.0
    width_m: float = 100.0
    height_m: float = 10.5
    num_floors: int = 1
    bay_spacing_m: float = 8.0
    plot_area_sqm: float = 32000.0
    building_components: List[str] = Field(default_factory=lambda: [
        "Production Block", "Warehouse", "Cold Store", "Utilities Block", "Admin Building",
    ])
    # Step 3 - structural & site
    soil_type: str = "Medium Dense Sand"
    sbc_soil_type: str = "Hard Stone"           # Bearing capacity type
    soil_hardness: str = "Medium"               # Hard / Medium / Soft
    foundation_type: str = "Raft Foundation"
    floor_load_kn: float = 5.0
    column_type: str = "Steel"
    roof_type: str = "PEB + Insulated Panel"
    seismic_zone: str = "Zone 0 (Very Low)"
    wind_zone: str = "Zone 2"
    wind_speed_ms: float = 24.0
    gwt_depth: str = "Medium (3-8 m)"
    # Step 4 - utilities & process
    utility_scope: List[str] = Field(default_factory=lambda: [
        "Boiler House", "Chiller Plant", "HVAC System", "Air Compressors",
        "Water Treatment Plant", "Fire Fighting System", "Electrical Substation",
    ])
    production_capacity_tpd: float = 120.0
    annual_output_mt: float = 36000.0
    # Chocolate-specific
    cooling_tunnel_load_tr: float = 180.0
    tempering_utility_demand: str = "Medium"
    humidity_controlled_pct: float = 40.0
    chocolate_storage_temp_c: float = 16.0
    process_hot_water_lph: float = 2500.0
    # Biscuit-specific
    oven_capacity_kg_hr: float = 1200.0
    fuel_type: str = "PNG"                      # PNG / LPG / Diesel / Biomass
    baking_line_qty: int = 2
    compressed_air_demand_cfm: float = 1500.0
    dust_collection_required: bool = True
    cooling_conveyor_load: str = "Standard"
    # Step 5 - infra & site
    include_roads: bool = True
    include_landscaping: bool = True
    include_fence: bool = True
    land_area_sqm: float = 32000.0
    ground_coverage_pct: float = 58.0
    far_fsi: float = 1.2
    water_availability: str = "Municipal + Borewell"
    grid_reliability: str = "Good"
    ambient_temp_range: str = "Temperate (5°C - 30°C)"
    relative_humidity_pct: float = 70.0
    # Complexity toggles
    complexity: Dict[str, bool] = Field(default_factory=lambda: {
        "seismic_zone_high": False, "high_humidity": False, "cold_region": False,
        "brownfield": False, "gmp_hygienic": True, "explosion_risk": False,
        "utility_redundancy": True, "high_floor_load": False, "remote_site": False,
    })
    # Display
    currency: str = "USD"
    base_unit: str = "mm"
    contingency_pct: float = 8.0


class Estimate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    inputs: Dict[str, Any]
    result: Dict[str, Any]
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ---------- FX Rates ----------
_fx_cache: Dict[str, Any] = {"ts": 0, "rates": None}

async def get_fx_rates() -> Dict[str, float]:
    """Fetch USD-based FX rates. Cache for 1 hour. Fallback to static."""
    import time
    now = time.time()
    if _fx_cache["rates"] and now - _fx_cache["ts"] < 3600:
        return _fx_cache["rates"]
    fallback = {
        "USD": 1.0, "EUR": 0.919, "GBP": 0.786, "INR": 83.4, "JPY": 149.8,
        "AUD": 1.52, "CAD": 1.36, "CHF": 0.88, "CNY": 7.24, "SGD": 1.34,
        "AED": 3.67, "ZAR": 18.5, "BRL": 4.95, "MXN": 17.1,
    }
    try:
        async with httpx.AsyncClient(timeout=6.0) as c:
            r = await c.get("https://open.er-api.com/v6/latest/USD")
            data = r.json()
            if data.get("result") == "success":
                rates = {k: v for k, v in data["rates"].items() if k in CURRENCY_SYMBOLS}
                _fx_cache["rates"] = rates
                _fx_cache["ts"] = now
                return rates
    except Exception as e:
        logging.warning(f"FX API failed, using fallback: {e}")
    _fx_cache["rates"] = fallback
    _fx_cache["ts"] = now
    return fallback


# ---------- Live commodity / material index ----------
_rate_index_cache: Dict[str, Any] = {"ts": 0, "data": None}

async def get_live_rate_index() -> Dict[str, Any]:
    """Fetch live copper price (USD/lb) from api.gold-api.com as a proxy for
    construction material cost index. Copper is a well-established leading
    indicator for steel + electrical + HVAC costs. Free, keyless endpoint.
    Cache 30 min. Fallback to gold, then to baseline."""
    import time
    now = time.time()
    if _rate_index_cache["data"] and now - _rate_index_cache["ts"] < 1800:
        return _rate_index_cache["data"]

    # Baseline copper price (USD/lb, COMEX HG) - anchors the index at 1.00
    BASELINE_COPPER_USD_LB = 4.50
    BASELINE_GOLD_USD_OZ   = 2100.0
    data = {"source": "fallback", "commodity": "copper",
            "price": BASELINE_COPPER_USD_LB, "price_unit": "USD/lb",
            "material_index": 1.00, "delta_pct": 0.0,
            "fetched_at": datetime.now(timezone.utc).isoformat()}

    async def _try(url: str, symbol: str, baseline: float, unit: str):
        async with httpx.AsyncClient(timeout=6.0) as c:
            r = await c.get(url)
            if r.status_code != 200:
                return None
            j = r.json()
            price = float(j.get("price") or 0)
            if price <= 0:
                return None
            idx = max(0.80, min(1.35, price / baseline))
            return {
                "source": "api.gold-api.com",
                "commodity": symbol,
                "price": round(price, 4),
                "price_unit": unit,
                "material_index": round(idx, 4),
                "delta_pct": round((idx - 1.0) * 100, 2),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }

    try:
        d = await _try("https://api.gold-api.com/price/HG", "copper", BASELINE_COPPER_USD_LB, "USD/lb")
        if not d:
            d = await _try("https://api.gold-api.com/price/XAU", "gold", BASELINE_GOLD_USD_OZ, "USD/oz")
        if d:
            data = d
    except Exception as e:
        logging.warning(f"Rate-index API failed, using fallback: {e}")

    _rate_index_cache["data"] = data
    _rate_index_cache["ts"] = now
    return data


# ---------- Fine-grained input multipliers ----------
FOUNDATION_M   = {"Isolated Footing": 0.90, "Combined Footing": 0.95, "Raft Foundation": 1.00, "Pile Foundation": 1.28, "Engineering Fill": 1.10}
SOIL_HARDNESS_M= {"Hard": 0.92, "Medium": 1.00, "Soft": 1.14}
SBC_M          = {"Black Cotton": 1.15, "Silty": 1.08, "Reclaimed / Engineering Fill": 1.20, "Hard Stone": 0.90}
GWT_M          = {"Shallow (<3 m)": 1.18, "Medium (3-8 m)": 1.05, "Deep (>8 m)": 1.00}
WIND_ZONE_M    = {"Zone 1 (Low)": 0.96, "Zone 2": 1.00, "Zone 3": 1.05, "Zone 4 (High)": 1.10, "Zone 5 (Cyclonic)": 1.18}
SEISMIC_ZONE_M = {"Zone 0 (Very Low)": 0.97, "Zone I": 1.00, "Zone II": 1.03, "Zone III": 1.06, "Zone IV": 1.10, "Zone V (High)": 1.16}
ROOF_M         = {"PEB + Insulated Panel": 1.00, "RCC Slab": 1.22, "Metal Deck + Insulation": 1.05}
COLUMN_M       = {"RCC": 1.12, "Steel": 1.00, "Composite": 1.18}
FUEL_M         = {"PNG": 1.00, "LPG": 1.08, "Diesel": 1.15, "Biomass": 0.92, "Electric": 1.28}
GRID_DG_ADD    = {"Excellent": 0.00, "Good": 0.02, "Average": 0.06, "Poor (frequent outages)": 0.12}
WATER_AVAIL_M  = {"Municipal": 0.85, "Municipal + Borewell": 1.00, "Borewell": 1.08, "Tanker": 1.20, "Recycled + Fresh": 1.10, "Limited": 1.25}
AMBIENT_HVAC_M = {"Tropical (25°C - 40°C)": 1.15, "Temperate (5°C - 30°C)": 1.00, "Cold (-10°C - 15°C)": 1.08, "Hot Arid (30°C - 48°C)": 1.20, "Cool Temperate (0°C - 22°C)": 1.05}
BUILDING_TYPE_M= {"Industrial Shed": 0.88, "RCC Industrial Building": 1.10, "Industrial Building (RCC + PEB)": 1.00, "Warehouse": 0.82, "Utility / Admin Block": 0.96, "Mezzanine": 0.90, "Hybrid": 1.05}
PROJECT_TYPE_M = {"Greenfield": 1.00, "Brownfield / Expansion": 0.94, "Retrofit / Capacity Upgrade": 0.72}
INDUSTRY_TYPE_M= {"Food": 1.00, "FMCG": 0.92, "Warehouse / Logistics": 0.78, "Process Building": 1.15}
SOIL_TYPE_M    = {"Black Cotton": 1.12, "Silty": 1.06, "Reclaimed / Engineering Fill": 1.18, "Hard Stone": 0.92, "Medium Dense Sand": 1.00, "Loose Sand": 1.08, "Clayey": 1.05}
TEMPERING_M    = {"Low": 0.94, "Medium": 1.00, "High": 1.10, "Very High": 1.22}
CONVEYOR_M     = {"Light": 0.94, "Standard": 1.00, "Heavy Duty": 1.15}
CONTINENT_M    = {"Asia": 0.98, "Europe": 1.02, "North America": 1.05, "South America": 0.94, "Africa": 0.92, "Oceania": 1.06}

# Explicit map: UI utility_scope label -> canonical UTILITY_SYSTEMS row name
UTILITY_SCOPE_MAP = {
    "Boiler House":              "Steam & Boiler System",
    "Steam Distribution":        "Steam & Boiler System",
    "Chiller Plant":             "Refrigeration / Cold Chain",
    "HVAC System":               "Refrigeration / Cold Chain",
    "Air Compressors":           "Compressed Air System",
    "Process Piping":            "Compressed Air System",
    "Water Treatment Plant":     "Water Supply System",
    "Nitrogen Plant":            "Compressed Air System",
    "Fire Fighting System":      "Fire Fighting System",
    "Electrical Substation":     "Electrical Infrastructure",
    "DG Backup":                 "Electrical Infrastructure",
    "Solar Plant":               "Electrical Infrastructure",
    # legacy passthroughs (dialog may pass canonical name directly)
    "Steam & Boiler System":     "Steam & Boiler System",
    "Refrigeration / Cold Chain":"Refrigeration / Cold Chain",
    "Compressed Air System":     "Compressed Air System",
    "Water Supply System":       "Water Supply System",
    "ETP / STP System":          "ETP / STP System",
    "Electrical Infrastructure": "Electrical Infrastructure",
}


# ---------- Core estimator ----------
def compute_estimate(inp: ProjectInputs, live_index: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    built_up = inp.length_m * inp.width_m * inp.num_floors  # m² gross floor
    # Prefer land_area_sqm (framework) if it differs from legacy plot_area_sqm
    plot_area = max(inp.plot_area_sqm or 0, inp.land_area_sqm or 0) or inp.plot_area_sqm

    # ---- Global multipliers (region + tier + complexity + LIVE material index) ----
    region_m = REGION_MULTIPLIERS.get(inp.region, 1.0)
    tier_m = LOCATION_FACTOR.get(inp.location_tier, 1.0)
    project_type_m = PROJECT_TYPE_M.get(inp.project_type, 1.0)
    industry_m = INDUSTRY_TYPE_M.get(inp.industry_type, 1.0)
    continent_m = CONTINENT_M.get(inp.continent, 1.0)
    live_m = float((live_index or {}).get("material_index", 1.0))

    complexity_m = 1.0
    active_complexity = []
    for k, v in (inp.complexity or {}).items():
        if v and k in COMPLEXITY_FACTORS:
            complexity_m *= COMPLEXITY_FACTORS[k]
            active_complexity.append(k)

    global_m = region_m * tier_m * complexity_m * live_m * project_type_m * industry_m * (continent_m ** 0.3)

    # ---- Building multiplier (structural, site, envelope) ----
    # Bay spacing: smaller spacing => more columns => higher steel
    bay_m = (8.0 / max(2.0, inp.bay_spacing_m)) ** 0.15
    # Wind speed above 24 m/s bumps steel/roof
    wind_speed_m = 1.0 + max(0.0, (inp.wind_speed_ms - 24) * 0.008)
    # FAR/FSI > 1.5 requires more structural depth
    far_m = 1.0 + max(0.0, (inp.far_fsi - 1.5) * 0.06)

    building_m = (
        FOUNDATION_M.get(inp.foundation_type, 1.0)
        * SOIL_HARDNESS_M.get(inp.soil_hardness, 1.0)
        * SBC_M.get(inp.sbc_soil_type, 1.0)
        * SOIL_TYPE_M.get(inp.soil_type, 1.0)
        * GWT_M.get(inp.gwt_depth, 1.0)
        * WIND_ZONE_M.get(inp.wind_zone, 1.0)
        * SEISMIC_ZONE_M.get(inp.seismic_zone, 1.0)
        * COLUMN_M.get(inp.column_type, 1.0)
        * ROOF_M.get(inp.roof_type, 1.0)
        * BUILDING_TYPE_M.get(inp.building_type, 1.0)
        * bay_m
        * wind_speed_m
        * far_m
    ) ** (1.0 / 2.5)   # geometric moderation - avoid extreme compounding

    # ---- Utility multiplier (fuel, water, grid, ambient, humidity) ----
    humidity_m = 1.0 + max(0.0, (inp.relative_humidity_pct - 70) * 0.005)
    utility_m = (
        FUEL_M.get(inp.fuel_type, 1.0)
        * WATER_AVAIL_M.get(inp.water_availability, 1.0)
        * AMBIENT_HVAC_M.get(inp.ambient_temp_range, 1.0) ** 0.6
        * (1.0 + GRID_DG_ADD.get(inp.grid_reliability, 0.0))
        * humidity_m
    )

    # ---- Floor-load adder (>5 kN significant) ----
    if inp.floor_load_kn > 5:
        building_m *= 1.0 + (inp.floor_load_kn - 5) * 0.012

    # ---- Building components add scope (multi-select) ----
    comp_scope_adder = 1.0 + max(0, (len(inp.building_components or []) - 3)) * 0.03

    # Auto quantity take-off (heuristic ratios) - proportional to built-up area
    a = built_up
    perimeter = 2 * (inp.length_m + inp.width_m)
    boq_rows: List[Dict[str, Any]] = []

    # Landscaping quantity from Ground Coverage / plot area
    coverage_frac = max(0.0, min(1.0, (inp.ground_coverage_pct or 0) / 100.0))
    landscape_qty = plot_area * max(0.0, (1.0 - coverage_frac)) if inp.include_landscaping else 0

    qty_map = {
        "Excavation":                     a * 0.65,
        "PCC (M10)":                      a * 0.10,
        "RCC Foundation (Raft)":          a * 0.42,
        "Structural Steel (PEB)":         a * 0.055,
        "RCC Superstructure":             a * 0.24 * (inp.num_floors - 1 if inp.num_floors > 1 else 0.15),
        "Roofing (Insulated Panel)":      a,
        "Flooring (Epoxy + PU)":          a,
        "Walls (Block + Plaster + Tile)": perimeter * inp.height_m * inp.num_floors,
        "Plumbing & Sanitary":            1,
        "External Works & Roads":         plot_area * 0.28 if inp.include_roads else 0,
        "Compound Wall / Fence":          (perimeter + 200) if inp.include_fence else 0,
        "Landscaping":                    landscape_qty,
    }

    building_total = 0.0
    for activity, unit, base_rate, category in CIVIL_ACTIVITIES:
        qty = round(qty_map.get(activity, 0), 2)
        rate = round(base_rate * global_m * building_m, 2)
        amount = round(qty * rate, 2)
        if amount > 0:
            boq_rows.append({
                "activity": activity, "unit": unit, "quantity": qty,
                "rate": rate, "amount": amount, "category": category,
            })
            building_total += amount

    building_total *= comp_scope_adder

    # Product category preset shifts utilities share
    preset = INDUSTRY_PRESETS.get(inp.product_category, INDUSTRY_PRESETS.get("Chocolate Plant", {"utilities_pct": 0.35}))

    # Utilities cost (scope-filtered) using explicit UI-label -> canonical map
    scope_canonical = set()
    for label in (inp.utility_scope or []):
        canonical = UTILITY_SCOPE_MAP.get(label)
        if canonical:
            scope_canonical.add(canonical)

    utilities_total = 0.0
    utilities_rows = []
    for name, unit, base_rate in UTILITY_SYSTEMS:
        if name not in scope_canonical:
            continue
        cap_scale = max(0.5, (inp.production_capacity_tpd / 100.0))
        # Annual output slightly scales utility sizing
        output_scale = 1.0 + max(0.0, (inp.annual_output_mt - 36000) / 200000.0)
        amount = round(base_rate * global_m * utility_m * cap_scale * output_scale, 2)
        utilities_rows.append({"name": name, "unit": unit, "amount": amount})
        utilities_total += amount

    # Chocolate-specific utility bump
    is_chocolate = ("chocolate" in (inp.product_category or "").lower() or "combo" in (inp.product_category or "").lower())
    is_biscuit = any(t in (inp.product_category or "").lower() for t in ["biscuit", "wafer", "cookie", "combo"])
    if is_chocolate:
        # Cooling tunnel + humidity + tempering demand + storage temp (colder -> more chiller)
        storage_bump = max(1.0, (18.0 - inp.chocolate_storage_temp_c) * 0.02 + 1.0)
        hot_water_bump = 1.0 + (inp.process_hot_water_lph / 50000.0)
        temper_bump = TEMPERING_M.get(inp.tempering_utility_demand, 1.0)
        choco_bump = (
            1.0 + (inp.cooling_tunnel_load_tr / 1000.0)
            + (inp.humidity_controlled_pct / 500.0)
        ) * storage_bump * hot_water_bump * temper_bump
        utilities_total *= choco_bump
        for u in utilities_rows:
            u["amount"] = round(u["amount"] * choco_bump, 2)
    if is_biscuit:
        # Oven + baking lines + conveyor load + dust collection
        conveyor_bump = CONVEYOR_M.get(inp.cooling_conveyor_load, 1.0)
        dust_bump = 1.04 if inp.dust_collection_required else 1.0
        biscuit_bump = (
            1.0 + (inp.oven_capacity_kg_hr / 20000.0)
            + (inp.baking_line_qty * 0.02)
        ) * conveyor_bump * dust_bump
        utilities_total *= biscuit_bump
        for u in utilities_rows:
            u["amount"] = round(u["amount"] * biscuit_bump, 2)

    if utilities_total > 0:
        boq_rows.append({
            "activity": "Utilities & Process Systems", "unit": "LS", "quantity": 1,
            "rate": round(utilities_total, 2), "amount": round(utilities_total, 2),
            "category": "Utilities",
        })

    infra_pct_of_bldg = 0.14
    infra_total = round(building_total * infra_pct_of_bldg, 2)
    boq_rows.append({
        "activity": "Infra Works & External", "unit": "LS", "quantity": 1,
        "rate": infra_total, "amount": infra_total, "category": "Infra",
    })

    compliance_total = round((building_total + utilities_total) * COMPLIANCE_ADDER_PCT, 2)
    boq_rows.append({
        "activity": "Compliance (GMP Finishes)", "unit": "LS", "quantity": 1,
        "rate": compliance_total, "amount": compliance_total, "category": "Compliance",
    })

    subtotal = building_total + utilities_total + infra_total + compliance_total
    other_fees = round(subtotal * 0.06, 2)
    boq_rows.append({
        "activity": "Design + PM + Other Fees", "unit": "LS", "quantity": 1,
        "rate": other_fees, "amount": other_fees, "category": "Other",
    })

    subtotal += other_fees
    contingency = round(subtotal * (inp.contingency_pct / 100.0), 2)
    total = subtotal + contingency

    # Confidence score
    confidence = 92
    if inp.project_type == "Brownfield / Expansion":
        confidence -= 6
    if inp.project_type == "Retrofit / Capacity Upgrade":
        confidence -= 4
    if inp.location_tier == "Remote":
        confidence -= 4
    if (inp.complexity or {}).get("brownfield"): confidence -= 3
    if (inp.complexity or {}).get("explosion_risk"): confidence -= 3
    if (inp.complexity or {}).get("remote_site"): confidence -= 2
    if inp.production_capacity_tpd == 0:
        confidence -= 8
    if inp.grid_reliability == "Poor (frequent outages)":
        confidence -= 2
    if (live_index or {}).get("source") == "fallback":
        confidence -= 1
    confidence = max(45, min(96, confidence))
    conf_label = "High" if confidence >= 85 else "Medium" if confidence >= 70 else "Low"

    def pct(x): return round((x / total) * 100, 2) if total > 0 else 0
    breakdown = [
        {"name": "Civil Building", "value": round(building_total, 2), "pct": pct(building_total)},
        {"name": "Utilities & Process", "value": round(utilities_total, 2), "pct": pct(utilities_total)},
        {"name": "Infra & External", "value": infra_total, "pct": pct(infra_total)},
        {"name": "Compliance (GMP)", "value": compliance_total, "pct": pct(compliance_total)},
        {"name": "Other & Fees", "value": other_fees, "pct": pct(other_fees)},
        {"name": "Contingency", "value": contingency, "pct": pct(contingency)},
    ]

    sorted_boq = sorted(boq_rows, key=lambda r: r["amount"], reverse=True)
    top12 = []
    for i, r in enumerate(sorted_boq[:12], start=1):
        r2 = dict(r)
        r2["rank"] = i
        r2["pct_of_total"] = round((r["amount"] / total) * 100, 2) if total > 0 else 0
        top12.append(r2)

    duration = round(8 + built_up / 6000 + (0.15 * inp.num_floors), 1)

    cap = inp.production_capacity_tpd
    utility_demand = {
        "water_kld": round(0.35 * cap * 10 + 20, 0),
        "steam_kg_hr": round(35 * cap + 400 + (inp.oven_capacity_kg_hr * 0.15 if is_biscuit else 0), 0),
        "chiller_tr": round(3.5 * cap + (inp.cooling_tunnel_load_tr if is_chocolate else 0), 0),
        "power_kva": round(23 * cap + 300, 0),
        "compressed_air_cfm": round(12 * cap + 300 + (inp.compressed_air_demand_cfm * 0.3 if is_biscuit else 0), 0),
        "etp_kld": round(1.5 * cap, 0),
        "fire_water_m3": 600,
    }

    # Cost trend S-curve
    n = int(round(duration))
    n = max(6, min(24, n))
    import math
    trend = []
    start = datetime.now(timezone.utc)
    cum = 0
    for i in range(n):
        x = (i + 1) / n
        cum_pct = 1 / (1 + math.exp(-10 * (x - 0.5)))
        period_amount = round(total * cum_pct - cum, 0)
        cum = total * cum_pct
        month = (start.month - 1 + i) % 12 + 1
        year_off = (start.month - 1 + i) // 12
        label = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][month - 1]
        trend.append({
            "period": f"{label} '{str(start.year + year_off)[-2:]}",
            "base": round(period_amount * 0.96, 0),
            "current": round(period_amount, 0),
            "benchmark": round(period_amount * 1.05, 0),
        })

    region_benchmark_delta = round((global_m - 1.0) * 100, 1)

    return {
        "totals": {
            "total_project_cost": round(total, 2),
            "cost_per_sqm": round(total / built_up, 2) if built_up else 0,
            "cost_per_mt": round(total / inp.annual_output_mt, 2) if inp.annual_output_mt else 0,
            "duration_months": duration,
            "confidence_score": confidence,
            "confidence_label": conf_label,
            "contingency": contingency,
            "contingency_pct": inp.contingency_pct,
            "region_benchmark_delta_pct": region_benchmark_delta,
            "built_up_area_sqm": round(built_up, 2),
            "plot_area_sqm": plot_area,
        },
        "breakdown": breakdown,
        "boq": sorted_boq,
        "top_cost_items": top12,
        "utilities": utilities_rows,
        "utilities_total": round(utilities_total, 2),
        "utility_demand": utility_demand,
        "cost_trend": trend,
        "multipliers": {
            "region": region_m, "tier": tier_m,
            "complexity": round(complexity_m, 4),
            "building": round(building_m, 4),
            "utility": round(utility_m, 4),
            "project_type": project_type_m,
            "live_material_index": live_m,
            "combined": round(global_m, 4),
        },
        "active_complexity": active_complexity,
        "live_rate_index": live_index or {},
    }


# ---------- AI insights ----------
async def generate_ai_insights(inp: ProjectInputs, result: Dict[str, Any]) -> Dict[str, Any]:
    """Use Claude Sonnet 4.5 to generate Key Assumptions, Risk Drivers, Optimization tips."""
    key = os.environ.get("EMERGENT_LLM_KEY")
    if not key:
        return _fallback_insights(inp, result)
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage

        session_id = f"est-{uuid.uuid4().hex[:12]}"
        system_message = (
            "You are a senior construction cost estimator for food-industry manufacturing plants. "
            "Given project inputs and computed estimate, produce concise, JSON-only response with "
            "keys: assumptions (array of 6 short bullets), risks (array of 5 short bullets), "
            "optimizations (array of 4 short bullets), executive_summary (2-3 sentence string). "
            "Return ONLY valid JSON, no markdown fences."
        )
        chat = LlmChat(api_key=key, session_id=session_id, system_message=system_message).with_model(
            "anthropic", "claude-sonnet-4-5-20250929"
        )
        payload = {
            "project": {
                "name": inp.project_name, "type": inp.project_type, "industry": inp.industry_type,
                "location": f"{inp.location_city}, {inp.location_country}", "region": inp.region,
                "tier": inp.location_tier, "capacity_tpd": inp.production_capacity_tpd,
                "annual_mt": inp.annual_output_mt, "built_up_m2": result["totals"]["built_up_area_sqm"],
                "active_complexity": result.get("active_complexity", []),
            },
            "totals_usd": result["totals"],
            "breakdown": result["breakdown"],
        }
        msg = UserMessage(text=f"Project + estimate:\n{json.dumps(payload, indent=2)}\n\nReturn JSON only.")
        text = await chat.send_message(msg)
        # Extract JSON
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            data = json.loads(m.group(0))
            return {
                "assumptions": data.get("assumptions", [])[:8],
                "risks": data.get("risks", [])[:8],
                "optimizations": data.get("optimizations", [])[:6],
                "executive_summary": data.get("executive_summary", ""),
                "source": "ai",
            }
    except Exception as e:
        logging.warning(f"AI insight failed: {e}")
    return _fallback_insights(inp, result)


def _fallback_insights(inp: ProjectInputs, result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "assumptions": [
            "All dimensions in mm, all costs in USD",
            "Rates are inclusive of basic taxes (excl. VAT)",
            "Design basis as per Eurocodes & local standards",
            "Concept level quantities",
            "No night shift considered",
            "Excludes statutory approvals & financing cost",
        ],
        "risks": [
            "Steel price volatility in Europe",
            "Utility equipment lead time",
            "Environmental compliance escalation",
            "Import duty / logistics impact",
            "Skilled labor availability",
        ],
        "optimizations": [
            "Consider PEB alternative for superstructure to reduce steel tonnage",
            "Bulk-procure utility equipment across chocolate + biscuit lines",
            "Evaluate air-cooled vs water-cooled chiller for lower CapEx",
            "Explore solar rooftop for utility power reduction (5-yr payback)",
        ],
        "executive_summary": (
            f"Concept-stage estimate for a {inp.production_capacity_tpd:.0f} TPD "
            f"{inp.industry_type.lower()} in {inp.location_city}, {inp.location_country}. "
            f"Total project cost is USD {result['totals']['total_project_cost']:,.0f} "
            f"with {result['totals']['confidence_label'].lower()} confidence."
        ),
        "source": "fallback",
    }


# ---------- Routes ----------
@api_router.get("/")
async def root():
    return {"message": "Estimator API online", "version": "1.0.0"}


@api_router.get("/estimator/fx-rates")
async def fx_rates():
    rates = await get_fx_rates()
    return {"base": "USD", "rates": rates, "symbols": CURRENCY_SYMBOLS}


@api_router.get("/estimator/reference")
async def reference_data():
    """Return dropdown / static reference data for the wizard - grouped by wizard step."""
    return {
        # ---- Stage-based cost intelligence (framework) ----
        "regions": list(REGION_MULTIPLIERS.keys()),         # Stage 2 - Region
        "continents": ["Asia", "Europe", "North America", "South America", "Africa", "Oceania"],  # Stage 3
        "tiers": list(LOCATION_FACTOR.keys()),              # Stage 1 - Country tier
        # ---- Step 1: Project Identification ----
        "project_types": ["Greenfield", "Brownfield / Expansion", "Retrofit / Capacity Upgrade"],
        "industries": ["Food", "FMCG", "Warehouse / Logistics", "Process Building"],
        "product_categories": list(INDUSTRY_PRESETS.keys()),
        # ---- Step 2: Building Geometry ----
        "building_types": [
            "Industrial Shed", "RCC Industrial Building", "Industrial Building (RCC + PEB)",
            "Warehouse", "Utility / Admin Block", "Mezzanine", "Hybrid",
        ],
        "building_components": [
            "Production Block", "Warehouse", "Cold Store", "Utilities Block",
            "Admin Building", "ETP / STP", "R&D Lab", "Packaging Hall",
        ],
        # ---- Step 3: Structural & Site ----
        "foundation_types": [
            "Isolated Footing", "Combined Footing", "Raft Foundation",
            "Pile Foundation", "Engineering Fill",
        ],
        "sbc_soil_types": [
            "Black Cotton", "Silty", "Reclaimed / Engineering Fill", "Hard Stone",
        ],
        "soil_types": [
            "Black Cotton", "Silty", "Reclaimed / Engineering Fill",
            "Hard Stone", "Medium Dense Sand", "Loose Sand", "Clayey",
        ],
        "soil_hardness": ["Hard", "Medium", "Soft"],
        "roof_types": ["PEB + Insulated Panel", "RCC Slab", "Metal Deck + Insulation"],
        "column_types": ["RCC", "Steel", "Composite"],
        "seismic_zones": [
            "Zone 0 (Very Low)", "Zone I", "Zone II", "Zone III",
            "Zone IV", "Zone V (High)",
        ],
        "wind_zones": [
            "Zone 1 (Low)", "Zone 2", "Zone 3", "Zone 4 (High)", "Zone 5 (Cyclonic)",
        ],
        "gwt_depths": ["Shallow (<3 m)", "Medium (3-8 m)", "Deep (>8 m)"],
        # ---- Step 4: Utilities & Process ----
        "utility_scope": [
            "Boiler House", "Chiller Plant", "HVAC System", "Air Compressors",
            "Water Treatment Plant", "Nitrogen Plant", "Fire Fighting System",
            "Electrical Substation", "DG Backup", "Solar Plant",
            "Steam Distribution", "Process Piping",
        ],
        "fuel_types": ["PNG", "LPG", "Diesel", "Biomass", "Electric"],
        "tempering_utility_demand": ["Low", "Medium", "High", "Very High"],
        "cooling_conveyor_load": ["Light", "Standard", "Heavy Duty"],
        # ---- Step 5: Infra & Site ----
        "water_availability": [
            "Municipal", "Municipal + Borewell", "Borewell", "Tanker",
            "Recycled + Fresh", "Limited",
        ],
        "grid_reliability": ["Excellent", "Good", "Average", "Poor (frequent outages)"],
        "ambient_temp_ranges": [
            "Tropical (25°C - 40°C)", "Temperate (5°C - 30°C)", "Cold (-10°C - 15°C)",
            "Hot Arid (30°C - 48°C)", "Cool Temperate (0°C - 22°C)",
        ],
        # ---- Complexity toggles ----
        "complexity": [
            {"key": "seismic_zone_high", "label": "Seismic Zone High"},
            {"key": "high_humidity", "label": "High Humidity Region"},
            {"key": "cold_region", "label": "Cold Region"},
            {"key": "brownfield", "label": "Brownfield Tie-ins"},
            {"key": "gmp_hygienic", "label": "GMP / Hygienic Finish"},
            {"key": "explosion_risk", "label": "Explosion Risk / Dust Areas"},
            {"key": "utility_redundancy", "label": "Utility Redundancy (N+1)"},
            {"key": "high_floor_load", "label": "High Floor Load"},
            {"key": "remote_site", "label": "Remote Site"},
        ],
        "currencies": list(CURRENCY_SYMBOLS.keys()),
    }


@api_router.get("/estimator/rate-index")
async def rate_index():
    """Live construction material cost index (copper price proxy)."""
    return await get_live_rate_index()


@api_router.post("/estimator/insights")
async def insights(payload: Dict[str, Any]):
    """Return only AI insights for given inputs + result. Runs in parallel with
    the fast calculate path so KPIs update instantly."""
    inp_data = payload.get("inputs") or {}
    result = payload.get("result") or {}
    inp = ProjectInputs(**inp_data)
    ai = await generate_ai_insights(inp, result)
    return ai


@api_router.post("/estimator/calculate")
async def calculate(inp: ProjectInputs):
    live_index = await get_live_rate_index()
    result = compute_estimate(inp, live_index=live_index)
    ai = await generate_ai_insights(inp, result)
    result["insights"] = ai
    fx = await get_fx_rates()
    result["fx_rates"] = fx
    return result


@api_router.post("/estimator/calculate-fast")
async def calculate_fast(inp: ProjectInputs):
    """Same as calculate but skips AI (for live slider preview)."""
    live_index = await get_live_rate_index()
    return compute_estimate(inp, live_index=live_index)


@api_router.post("/estimator/save")
async def save_estimate(payload: Dict[str, Any]):
    inputs = payload.get("inputs")
    result = payload.get("result")
    if not inputs or not result:
        raise HTTPException(400, "inputs and result required")
    est = Estimate(inputs=inputs, result=result)
    doc = est.model_dump()
    await db.estimates.insert_one(doc)
    return {"id": est.id, "created_at": est.created_at}


@api_router.get("/estimator/list")
async def list_estimates():
    docs = await db.estimates.find({}, {"_id": 0}).sort("created_at", -1).to_list(50)
    return [{"id": d["id"], "created_at": d["created_at"],
             "project_name": d["inputs"].get("project_name", "Unnamed"),
             "total": d["result"]["totals"]["total_project_cost"]} for d in docs]


@api_router.get("/estimator/{est_id}")
async def get_estimate(est_id: str):
    doc = await db.estimates.find_one({"id": est_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "not found")
    return doc


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
