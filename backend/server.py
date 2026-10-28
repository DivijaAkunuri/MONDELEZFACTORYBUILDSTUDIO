'''from fastapi import FastAPI, APIRouter, HTTPException
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
import math
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict, model_validator
import httpx

from rate_data import (
    CIVIL_ACTIVITIES, UTILITY_SYSTEMS, REGION_MULTIPLIERS,
    LOCATION_FACTOR, COMPLEXITY_FACTORS, INDUSTRY_PRESETS,
    COMPLIANCE_ADDER_PCT, CONTINGENCY_PCT, CURRENCY_SYMBOLS,
    CITY_FACTORS, city_factor_lookup,
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
    industry_type: str = "FMCG"                 # Food / FMCG / Warehouse / Process Building
    product_category: str = "Chocolate Plant"   # Chocolate Plant / Biscuit Plant / ...
    location_city: str = "Hamburg"
    location_country: str = "Germany"
    region: str = "MEU"                      # Stage 2 region                   # Stage 3 world/continent
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
    "Production Block","Warehouse","Warehouse-Chocolate","Utilities Block","Admin Building","WWTP","R&D Lab","Packaging Hall",
    ])
    # Step 3 - structural & site
    
    sbc_soil_type: str = "Hard"           # Bearing capacity type               # Hard / Medium / Soft
    foundation_type: List[str] = Field(default_factory=lambda: ["Raft Foundation"])
    floor_load_kn: float = 5.0
    column_type: str = "Steel"
    roof_type: str = "PEB + Insulated Panel"
    roof_types_by_floor: List[List[str]] = Field(default_factory=lambda: [["PEB + Insulated Panel"]])
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
    # Employee & Staff Facilities
    num_employees: int = 0
    male_employees: int = 0
    female_employees: int = 0
    special_work_clothing: str = "Yes"
    work_shoes_required: str = "Yes"      
    @model_validator(mode="after")
    def validate_employee_counts(self):
        if min(self.num_employees, self.male_employees, self.female_employees) < 0:
            raise ValueError("Employee counts cannot be negative.")
        if self.male_employees + self.female_employees != self.num_employees:
            raise ValueError("Male Employees + Female Employees must equal Total Employees.")
        return self
    

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
    # Static fallback - refreshed 08/2026 (live rates come from open.er-api.com).
    # CZK added for the MDLZ benchmark (Excel contract rate was 21.63).
    fallback = {
        "USD": 1.0, "EUR": 0.90, "GBP": 0.77, "INR": 86.5, "JPY": 148.0,
        "AUD": 1.52, "CAD": 1.37, "CHF": 0.82, "CNY": 7.10, "SGD": 1.32,
        "AED": 3.6725, "ZAR": 18.8, "BRL": 5.40, "MXN": 18.6, "CZK": 21.63,
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

    # Baseline copper price (USD/lb, COMEX HG) - anchors the index at 1.00.
    # Updated to the 2026 copper market (~$4.85/lb) from the old $4.50 anchor.
    BASELINE_COPPER_USD_LB = 4.85
    BASELINE_GOLD_USD_OZ   = 3300.0
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
            d=None
        if d:
            data = d
    except Exception as e:
        logging.warning(f"Rate-index API failed, using fallback: {e}")

    _rate_index_cache["data"] = data
    _rate_index_cache["ts"] = now
    return data


# ---------- Fine-grained input multipliers ----------
FOUNDATION_M   = {"Isolated Footing": 0.90, "Raft Foundation": 1.00, "Pile Foundation": 1.28, "Engineering Fill": 1.10}
SBC_M          = {"Hard": 0.92,"Soft": 1.14}
GWT_M          = {"Shallow (<3 m)": 1.18, "Medium (3-8 m)": 1.05, "Deep (>8 m)": 1.00}
WIND_ZONE_M    = {"Zone 1 (Low)": 0.96, "Zone 2": 1.00, "Zone 3": 1.05, "Zone 4 (High)": 1.10, "Zone 5 (Cyclonic)": 1.18}
SEISMIC_ZONE_M = {"Zone 0 (Very Low)": 0.97, "Zone I": 1.00, "Zone II": 1.03, "Zone III": 1.06, "Zone IV": 1.10, "Zone V (High)": 1.16}
ROOF_M         = {"PEB + Insulated Panel": 1.00, "RCC Slab": 1.22, "Metal Deck + Insulation": 1.05}
COLUMN_M       = {"RCC": 1.12, "Steel": 1.00, "RCC+Steel": 1.18}
FUEL_M         = {"PNG": 1.00, "LPG": 1.08, "Diesel": 1.15, "Biomass": 0.92, "Electric": 1.28}
GRID_DG_ADD    = {"Excellent": 0.00, "Good": 0.02, "Average": 0.06, "Poor (frequent outages)": 0.12}
WATER_AVAIL_M  = {"Municipal": 0.85, "Municipal + Borewell": 1.00, "Borewell": 1.08, "Tanker": 1.20, "Recycled + Fresh": 1.10, "Limited": 1.25}
AMBIENT_HVAC_M = {"Tropical (25°C - 40°C)": 1.15, "Temperate (5°C - 30°C)": 1.00, "Cold (-10°C - 15°C)": 1.08, "Hot Arid (30°C - 48°C)": 1.20, "Cool Temperate (0°C - 22°C)": 1.05}
BUILDING_TYPE_M= {"RCC Industrial Building": 1.10, "Industrial Building (RCC + PEB)": 1.00, "Warehouse-PEB": 0.82}
PROJECT_TYPE_M = {"Greenfield": 1.00, "Brownfield / Expansion": 0.94}
INDUSTRY_TYPE_M= { "FMCG": 0.92}
TEMPERING_M    = {"Low": 0.94, "Medium": 1.00, "High": 1.10, "Very High": 1.22}
CONVEYOR_M     = {"Light": 0.94, "Standard": 1.00, "Heavy Duty": 1.15}

# ---------- Employee & Staff Facilities ----------
# ---------- Employee & Staff Facilities ----------
# ---------- Employee & Staff Facilities ----------
def calculate_employee_facilities(inp: ProjectInputs) -> Dict[str, Any]:
    employees = max(0, int(inp.num_employees or 0))
    male = max(0, int(inp.male_employees or 0))
    female = max(0, int(inp.female_employees or 0))
    clothing = str(inp.special_work_clothing or "Yes").strip().lower() == "yes"
    shoes = str(inp.work_shoes_required or "Yes").strip().lower() == "yes"
    country = str(inp.location_country or "").strip()

    if employees <= 0:
        return {
            "employees": 0, "male": 0, "female": 0, "lockers": 0,
            "changing_area_sqm": 0, "locker_area_sqm": 0,
            "shoe_storage_area_sqm": 0, "total_area_sqm": 0,
            "seating": 0, "street_shoe_storage_positions": 0,
            "work_shoe_storage_positions": 0, "items": [],
            "design_basis": "No employees entered",
            "facility_location": "Admin Building",
            "locker_dimension_m": {"width": 0.30, "depth": 0.50},
            "locker_dimension_basis": "Germany ASR A4.1 reference module; verify local requirement",
            "shoe_storage_dimension_m": None, "shoe_storage_modules": 0,
            "shoe_storage_basis": "Not required", "changing_room_zones": 0,
            "changing_room_doors": 0, "privacy_partitions": 0,
            "facility_scope_status": "No employee facility scope generated",
            "wet_area_scope": "Not automatically assumed; no shower/wet-area input is provided",
            "fire_safety_scope": "Not applicable",
            "hvac_scope": "Not applicable",
        }

    lockers = employees

    # Individual locker module. Germany ASR A4.1 provides a 0.30 m x 0.50 m
    # reference locker footprint; other countries are treated as planning basis
    # unless a verified local dimensional requirement is available.
    locker_width_m = 0.30
    locker_depth_m = 0.50
    locker_area = lockers * locker_width_m * locker_depth_m
    locker_dimension_basis = (
        "Germany ASR A4.1 reference module"
        if country == "Germany"
        else "Planning module; verify local requirement"
    )

    # Changing-room movement area.
    # The rate is deliberately initialized before any country branching so
    # movement_area can never be undefined.
    movement_rate = 0.50
    rule_basis = "0.50 m²/user planning basis"

    if country == "Canada":
        movement_rate = 0.40
        rule_basis = "Canada regulatory benchmark: 0.40 m²/user"
    elif country == "Germany":
        movement_rate = 0.50
        rule_basis = "Germany ASR A4.1: 0.50 m²/user"

    movement_area = employees * movement_rate if clothing else 0.0
    changing_area = movement_area

    # Seating is required only when a dedicated changing room is provided.
    seating = math.ceil(employees / 4) if clothing else 0

    # Separate storage positions for street shoes and work shoes/boots.
    shoe_width_m = 0.30 if shoes else 0.0
    shoe_depth_m = 0.35 if shoes else 0.0
    shoe_storage_modules = 2 if shoes else 0
    shoe_storage_area = (
        employees * shoe_width_m * shoe_depth_m * shoe_storage_modules
    )
    shoe_storage_basis = (
        "Planning module; verify local requirement" if shoes else "Not required"
    )

    street_shoe_positions = employees if shoes else 0
    work_shoe_positions = employees if shoes else 0

    # The total facility area represents clear changing movement plus
    # locker and shoe-storage footprints. It does NOT enlarge the plant
    # footprint automatically; the facilities are located within the
    # Admin Building.
    total_area = changing_area + locker_area + shoe_storage_area

    items = [
        {"item": "Individual Employee Lockers", "quantity": lockers, "unit": "No."},
        {"item": "Male Employee Lockers", "quantity": male, "unit": "No."},
        {"item": "Female Employee Lockers", "quantity": female, "unit": "No."},
        {"item": "Locker Storage Area", "quantity": round(locker_area, 2), "unit": "m²"},
        {"item": "Employee Facility Floor Finish", "quantity": round(total_area, 2), "unit": "m²"},
        {"item": "Employee Facility Ceiling Finish", "quantity": round(total_area, 2), "unit": "m²"},
        {"item": "Employee Facility Lighting", "quantity": round(total_area, 2), "unit": "m² planning area"},
        {"item": "Employee Facility Electrical", "quantity": round(total_area, 2), "unit": "m² planning area"},
    ]

    if shoes:
        items.extend([
            {"item": "Outside / Street Shoe Storage", "quantity": street_shoe_positions, "unit": "Employee positions"},
            {"item": "Non-Marking Work Shoe / Boot Storage", "quantity": work_shoe_positions, "unit": "Employee positions"},
            {"item": "Shoe Storage Planning Area", "quantity": round(shoe_storage_area, 2), "unit": "m²"},
        ])

    if clothing:
        male_room = 1 if male > 0 else 0
        female_room = 1 if female > 0 else 0
        changing_rooms = male_room + female_room
        doors = changing_rooms
        privacy_partitions = max(0, changing_rooms - 1)

        items.extend([
            {"item": "Changing Room Zones", "quantity": changing_rooms, "unit": "No."},
            {"item": "Changing Room Doors", "quantity": doors, "unit": "No."},
        ])

        if privacy_partitions:
            items.append({
                "item": "Privacy / Gender Separation Partition",
                "quantity": privacy_partitions,
                "unit": "No."
            })

        items.extend([
            {"item": "Mechanical / Natural Ventilation Scope", "quantity": round(total_area, 2), "unit": "m² served area"},
            {"item": "Emergency / General Lighting Scope", "quantity": round(total_area, 2), "unit": "m² served area"},
            {"item": "Electrical Power / Small-Power Scope", "quantity": round(total_area, 2), "unit": "m² served area"},
            {"item": "Fire & Life Safety Coordination", "quantity": 1, "unit": "LS"},
            {"item": "Emergency Egress / Access Coordination", "quantity": 1, "unit": "LS"},
            {"item": "Room Construction / Finishes Coordination", "quantity": 1, "unit": "LS"},
        ])

    return {
        "employees": employees,
        "male": male,
        "female": female,
        "lockers": lockers,
        "changing_area_sqm": round(changing_area, 2),
        "locker_area_sqm": round(locker_area, 2),
        "shoe_storage_area_sqm": round(shoe_storage_area, 2),
        "total_area_sqm": round(total_area, 2),
        "seating": seating,
        "street_shoe_storage_positions": street_shoe_positions,
        "work_shoe_storage_positions": work_shoe_positions,
        "locker_sections": 2 if clothing else 1,
        "locker_dimension_m": {
            "width": locker_width_m,
            "depth": locker_depth_m,
        },
        "locker_dimension_basis": locker_dimension_basis,
        "shoe_storage_dimension_m": (
            {"width": shoe_width_m, "depth": shoe_depth_m} if shoes else None
        ),
        "shoe_storage_modules": shoe_storage_modules,
        "shoe_storage_basis": shoe_storage_basis,
        "changing_room_zones": (
            (1 if male > 0 else 0) + (1 if female > 0 else 0)
            if clothing else 0
        ),
        "changing_room_doors": (
            (1 if male > 0 else 0) + (1 if female > 0 else 0)
            if clothing else 0
        ),
        "privacy_partitions": (
            max(
                0,
                ((1 if male > 0 else 0) + (1 if female > 0 else 0)) - 1
            )
            if clothing else 0
        ),
        "facility_location": "Admin Building",
        "design_basis": rule_basis,
        "facility_scope_status": (
            "Calculated planning scope; statutory requirements and detailed engineering govern final design"
        ),
        "wet_area_scope": (
            "Not automatically assumed; no shower/wet-area input is provided"
        ),
        "fire_safety_scope": (
            "Included as coordination scope; final equipment quantities require building/fire-code design"
        ),
        "hvac_scope": (
            "Area served reported; equipment capacity requires engineering design inputs"
        ),
        "items": items,
    }
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
    built_up = inp.length_m * inp.width_m * inp.num_floors
    employee_facilities = calculate_employee_facilities(inp)
        # Employee & staff facilities

    # Prefer the larger framework land/plot value for external works.
    plot_area = (
        max(
            inp.plot_area_sqm or 0,
            inp.land_area_sqm or 0
        )
        or inp.plot_area_sqm
    )
    # ---- Global multipliers (region + tier + complexity + LIVE material index) ----
    region_m = REGION_MULTIPLIERS.get(inp.region, {}).get(inp.location_country, 1.0)
    tier_m = LOCATION_FACTOR.get(inp.location_tier, 1.0)
    project_type_m = PROJECT_TYPE_M.get(inp.project_type, 1.0)
    industry_m = INDUSTRY_TYPE_M.get(inp.industry_type, 1.0)
    live_m = float((live_index or {}).get("material_index", 1.0))

    # ---- City-specific factors (civil / mechanical / electrical / labour) ----
    city = city_factor_lookup(inp.location_city)
    city_civil = float(city["civil"])
    city_mech  = float(city["mechanical"])
    city_elec  = float(city["electrical"])
    city_lab   = float(city["labour"])
    # Labour weight in the total mix (~30% of construction cost is labour)
    LAB_W = 0.30
    # Effective per-discipline city multipliers = 70% discipline material + 30% labour
    civil_city_m = (1 - LAB_W) * city_civil + LAB_W * city_lab
    mech_city_m  = (1 - LAB_W) * city_mech  + LAB_W * city_lab
    elec_city_m  = (1 - LAB_W) * city_elec  + LAB_W * city_lab

    complexity_m = 1.0
    active_complexity = []
    for k, v in (inp.complexity or {}).items():
        if v and k in COMPLEXITY_FACTORS:
            complexity_m *= COMPLEXITY_FACTORS[k]
            active_complexity.append(k)

    global_m = region_m * tier_m * complexity_m * live_m * project_type_m * industry_m

    # ---- Building multiplier (structural, site, envelope) ----
    # Bay spacing: smaller spacing => more columns => higher steel
    bay_m = (8.0 / max(2.0, inp.bay_spacing_m)) ** 0.15
    # Wind speed above 24 m/s bumps steel/roof
    wind_speed_m = 1.0 + max(0.0, (inp.wind_speed_ms - 24) * 0.008)
    # FAR/FSI > 1.5 requires more structural depth
    far_m = 1.0 + max(0.0, (inp.far_fsi - 1.5) * 0.06)
    roof_floor_m = []
    for floor in range(max(1, inp.num_floors)):
       roofs = inp.roof_types_by_floor[floor] if floor < len(inp.roof_types_by_floor) else [inp.roof_type]
       roofs = roofs or [inp.roof_type]
       roof_floor_m.append(sum(ROOF_M.get(r, 1.0) for r in roofs) / len(roofs))
    roof_m = sum(roof_floor_m) / len(roof_floor_m)

    building_m = (
        max([FOUNDATION_M.get(f, 1.0) for f in inp.foundation_type] or [1.0])
        * SBC_M.get(inp.sbc_soil_type, 1.0)
        * GWT_M.get(inp.gwt_depth, 1.0)
        * WIND_ZONE_M.get(inp.wind_zone, 1.0)
        * SEISMIC_ZONE_M.get(inp.seismic_zone, 1.0)
        * COLUMN_M.get(inp.column_type, 1.0)
        * roof_m
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
        "Roofing (Insulated Panel)":      inp.length_m * inp.width_m * inp.num_floors,
        "Flooring (Epoxy + PU)":          a,
        "Walls (Block + Plaster + Tile)": perimeter * inp.height_m * inp.num_floors,
        "Plumbing & Sanitary":            1,
        "External Works & Roads":         plot_area * 0.28 if inp.include_roads else 0,
        "Compound Wall / Fence":          (perimeter + 200) if inp.include_fence else 0,
        "Landscaping":                    landscape_qty,
    }

    building_total = 0.0
    infra_total = 0.0
    for activity, unit, base_rate, category in CIVIL_ACTIVITIES:
        qty = round(qty_map.get(activity, 0), 2)
        rate = round(base_rate * global_m * building_m * civil_city_m, 2)
        amount = round(qty * rate, 2)
        if amount > 0:
            boq_rows.append({
                "activity": activity, "unit": unit, "quantity": qty,
                "rate": rate, "amount": amount, "category": category,
            })

        if category == "Infra":
            infra_total += amount
        elif category in ("Earthwork", "Foundation", "Superstructure", "Roofing", "Finishing", "MEP"):
            building_total += amount
    building_total = round(building_total, 2)
    infra_total = round(infra_total, 2)


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
    for name, unit, base_rate, discipline in UTILITY_SYSTEMS:
        if name not in scope_canonical:
            continue
        cap_scale = max(0.5, (inp.production_capacity_tpd / 100.0))
        # Annual output slightly scales utility sizing
        output_scale = 1.0 + max(0.0, (inp.annual_output_mt - 36000) / 200000.0)
        # Apply the correct city discipline factor per utility type
        disc_m = {"mechanical": mech_city_m, "electrical": elec_city_m, "civil": civil_city_m}.get(discipline, mech_city_m)
        if unit == "LS":
            amount = round(base_rate, 2)
        else:
            amount = round(base_rate * global_m * utility_m * disc_m, 2)
        utilities_rows.append({"name": name, "unit": unit, "amount": amount, "discipline": discipline})
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
            # Employee & staff facilities — scope only; cost is added separately
    # after verified facility rates are available.
        # Employee & staff facilities — construction scope priced from existing civil rates.
        # Employee & staff facilities — scope is reported separately.
    # Construction cost is carried through the building area calculation;
    # do not add a second civil charge here.
    if employee_facilities["employees"] > 0:
        boq_rows.append({
            "activity": "Employee & Staff Facilities",
            "unit": "LS",
            "quantity": 1,
            "rate": 0,
            "amount": 0,
            "category": "Employee Facilities",
            "scope": employee_facilities["items"],
            "employees": employee_facilities["employees"],
            "lockers": employee_facilities["lockers"],
            "area_sqm": employee_facilities["total_area_sqm"],
            "cost_status": "Scope only - included within Admin Building; no separate cost added",
            "cost_basis": "No verified employee-locker procurement rate in source rate database",
        })

    infra_total = round(infra_total, 2)
    infra_rows = [r for r in boq_rows if r.get("category") == "Infra"]

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
    def cost_per_sqm(x): return round(x / built_up, 2) if built_up > 0 else 0
    breakdown = [
        {"name": "Civil Building", "value": round(building_total, 2), "cost_per_sqm": cost_per_sqm(building_total), "pct": pct(building_total)},
        {"name": "Utilities & Process", "value": round(utilities_total, 2), "cost_per_sqm": cost_per_sqm(utilities_total), "pct": pct(utilities_total)},
        {"name": "Infra & External", "value": round(infra_total, 2), "cost_per_sqm": cost_per_sqm(infra_total), "pct": pct(infra_total)},
        {"name": "Compliance (GMP)", "value": round(compliance_total, 2), "cost_per_sqm": cost_per_sqm(compliance_total), "pct": pct(compliance_total)},
        {"name": "Other & Fees", "value": round(other_fees, 2), "cost_per_sqm": cost_per_sqm(other_fees), "pct": pct(other_fees)},
        {"name": "Contingency", "value": round(contingency, 2), "cost_per_sqm": cost_per_sqm(contingency), "pct": pct(contingency)},
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
        # Water Requirement
        "water_kld": round(max(20, 0.30 * cap * 10), 0),

        # Steam Requirement
        "steam_kg_hr": round(
            1800 if is_chocolate else
            2200 if is_biscuit else
            max(1200, cap * 15),
            0
        ),

        # Use USER INPUT instead of auto-sizing
        "chiller_tr": round(inp.cooling_tunnel_load_tr, 0),

        # Electrical Load
        "power_kva": round(max(500, cap * 12), 0),

        # Compressed Air
        "compressed_air_cfm": round(inp.compressed_air_demand_cfm, 0),

        # ETP
        "etp_kld": round(max(30, cap * 1.2), 0),

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
        "employee_facilities": employee_facilities,
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
            "employee_facility_area_sqm": round(employee_facilities["total_area_sqm"], 2),
            "employee_lockers": employee_facilities["lockers"],
            "employee_seating": employee_facilities["seating"],
            "employee_shoe_storage_positions": employee_facilities["street_shoe_storage_positions"] + employee_facilities["work_shoe_storage_positions"],
            "plot_area_sqm": plot_area,
        },
        "breakdown": breakdown,
        "employee_facilities": employee_facilities,
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
            "roof_types_by_floor": inp.roof_types_by_floor,
        },
        "active_complexity": active_complexity,
        "live_rate_index": live_index or {},
        "city_factors": {
            "matched": city.get("matched", False),
            "resolved": city.get("resolved"),
            "requested": inp.location_city,
            "civil": round(city_civil, 3),
            "mechanical": round(city_mech, 3),
            "electrical": round(city_elec, 3),
            "labour": round(city_lab, 3),
            "civil_effective": round(civil_city_m, 3),
            "mechanical_effective": round(mech_city_m, 3),
            "electrical_effective": round(elec_city_m, 3),
        },
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
        m = re.search(r"{[\s\S]*}", text)
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
        "regions": {region: list(countries.keys()) for region, countries in REGION_MULTIPLIERS.items()},        # Stage 2 - Region
        "tiers": list(LOCATION_FACTOR.keys()),              # Stage 1 - Country tier
        # ---- Step 1: Project Identification ----
        "project_types": ["Greenfield", "Brownfield / Expansion"],
        "industries": ["FMCG"],
        "product_categories": list(INDUSTRY_PRESETS.keys()),
        # ---- Step 2: Building Geometry ----
        "building_types": [
             "RCC Industrial Building", "Industrial Building (RCC + PEB)",
            "Warehouse-PEB",
        ],
        "building_components": [
            "Production Block", "Warehouse", "Warehouse-Chocolate", "Utilities Block",
            "Admin Building", "WWTP", "R&D Lab", "Packaging Hall",
        ],
        # ---- Step 3: Structural & Site ----
        "foundation_types": [
            "Isolated Footing", "Raft Foundation","Pile Foundation",
            "Engineering Fill",
        ],
        "sbc_soil_types": [
            "Hard","Soft",
        ],
        "roof_types": ["PEB + Insulated Panel", "RCC Slab", "Metal Deck + Insulation"],
        "column_types": ["RCC", "Steel", "RCC+Steel"],
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
        "cities": sorted({k.title() for k in CITY_FACTORS.keys()}),
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
    client.close() '''
    
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
import math
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict, model_validator
import httpx

from rate_data import (
    USA_BASE_CSA, USA_BASE_UTIL,
    COUNTRY_COST_FACTORS, get_country_cost_factors,
    UTILITY_SYSTEM_WEIGHTS, UTILITY_SYSTEMS,
    REGION_MULTIPLIERS, CIVIL_ACTIVITIES,
    LOCATION_FACTOR, COMPLEXITY_FACTORS,
    BENCHMARK_COMPLEXITY_M, BENCHMARK_STRUCTURAL_M, BENCHMARK_CITY,
    INDUSTRY_PRESETS, COMPLIANCE_ADDER_PCT, CONTINGENCY_PCT,
    CURRENCY_SYMBOLS, CITY_FACTORS, city_factor_lookup, get_benchmark_city_factors,
    PRODUCT_CATEGORY_LOAD, FLOOR_LOAD_REL_1500, get_floor_load_multiplier,
    EMPLOYEE_FACILITY_RATES, get_employee_facility_rates,
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()

origins = [
    "http://localhost:3000",
    "https://constructionestimator.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=(
        r"https://constructionestimator-[a-z0-9-]+-"
        r"divijaakunuri\.vercel\.app"
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api")
# ---------- Models ----------
class ProjectInputs(BaseModel):
    model_config = ConfigDict(extra="allow")
    # Step 1 - Project Identification
    project_name: str = "Chocolate & Bakery Manufacturing Plant"
    project_type: str = "Greenfield"           # Greenfield / Brownfield / Retrofit
    industry_type: str = "FMCG"                 # Food / FMCG / Warehouse / Process Building
    product_category: str = "Chocolate Plant"   # Chocolate Plant / Biscuit Plant / ...
    location_city: str = "Hamburg"
    location_country: str = "Germany"
    region: str = "MEU"                      # Stage 2 region                   # Stage 3 world/continent
    location_tier: str = "Metro"                # Metro / Non-Metro / Remote
    # Step 2 - geometry
    building_type: str = "Industrial Building (RCC + PEB)"
    length_m: float = 185.0
    width_m: float = 24.0
    height_m: float = 10.5
    num_floors: int = 1
    bay_spacing_m: float = 8.0
    building_components: List[str] = Field(default_factory=lambda: [
    "Admin Building","RM Warehouse","Production Floor","WH-Bakery","WH-Chocolate","Utilities Block","Territory Packaging Hall","R&D Center",
    ])
    # Step 3 - structural & site
    
    sbc_soil_type: str = "Hard"           # Bearing capacity type               # Hard / Medium / Soft
    foundation_type: List[str] = Field(default_factory=lambda: ["Raft Foundation"])
    column_type: str = "Steel"
    roof_type: str = "PEB + Insulated Panel"
    roof_types_by_floor: List[List[str]] = Field(default_factory=lambda: [["PEB + Insulated Panel"]])
    seismic_zone: str = "Zone 0 (Very Low)"
    wind_zone: str = "Zone 2"
    wind_speed_ms: float = 45.0
    gwt_depth: str = "Medium (3-8 m)"
    # Step 4 - utilities & process
    utility_scope: List[str] = Field(default_factory=lambda: [
        "Boiler House", "Chiller Plant", "HVAC System", "Air Compressors",
        "WTP", "Fire Fighting System", "Electrical Substation",
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
    # Employee & Staff Facilities
    num_employees: int = 0
    male_employees: int = 0
    female_employees: int = 0
    special_work_clothing: str = "Yes"
    work_shoes_required: str = "Yes" 
    work_shoes_required: str = "Yes"
    
    @model_validator(mode="after")
    def calculate_site_areas(self):
        length = self.length_m
        width = self.width_m
        land_area = self.land_area_sqm

        if not math.isfinite(length) or length <= 0:
           raise ValueError("Length must be greater than 0.")

        if not math.isfinite(width) or width <= 0:
           raise ValueError("Width must be greater than 0.")

        minimum_area = length * width

        if not math.isfinite(minimum_area) or minimum_area <= 0:
           raise ValueError("Length × Width must be greater than 0.")

        if not math.isfinite(land_area) or land_area <= 0:
           raise ValueError("Land Area must be greater than 0.")

        if land_area < minimum_area:
            raise ValueError(f"Land Area must be at least {minimum_area:g} m² ""(Length × Width).")
        return self

    @model_validator(mode="after")
    def validate_employee_counts(self):
        if min(
            self.num_employees,
            self.male_employees,
            self.female_employees,
        ) < 0:
            raise ValueError(
                "Employee counts cannot be negative."
            )

        if (
            self.male_employees + self.female_employees
            != self.num_employees
        ):
            raise ValueError(
                "Male Employees + Female Employees must equal "
                "Total Employees."
            )

        return self
    

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
    # Static fallback - refreshed 08/2026 (live rates come from open.er-api.com).
    # CZK added for the MDLZ benchmark (Excel contract rate was 21.63).
    fallback = {
        "USD": 1.0, "EUR": 0.90, "GBP": 0.77, "INR": 86.5, "JPY": 148.0,
        "AUD": 1.52, "CAD": 1.37, "CHF": 0.82, "CNY": 7.10, "SGD": 1.32,
        "AED": 3.6725, "ZAR": 18.8, "BRL": 5.40, "MXN": 18.6, "CZK": 21.63,
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

    # Baseline copper price (USD/lb, COMEX HG) - anchors the index at 1.00.
    # Updated to the 2026 copper market (~$4.85/lb) from the old $4.50 anchor.
    BASELINE_COPPER_USD_LB = 4.85
    BASELINE_GOLD_USD_OZ   = 3300.0
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
            d=None
        if d:
            data = d
    except Exception as e:
        logging.warning(f"Rate-index API failed, using fallback: {e}")

    _rate_index_cache["data"] = data
    _rate_index_cache["ts"] = now
    return data


# ---------- Fine-grained input multipliers ----------
FOUNDATION_M   = {"Isolated Footing": 0.90, "Raft Foundation": 1.00, "Pile Foundation": 1.28, "Engineering Fill": 1.10}
SBC_M          = {"Hard": 0.92,"Soft": 1.14}
GWT_M          = {"Shallow (<3 m)": 1.18, "Medium (3-8 m)": 1.05, "Deep (>8 m)": 1.00}
WIND_ZONE_M    = {"Zone 1 (Low)": 0.96, "Zone 2": 1.00, "Zone 3": 1.05, "Zone 4 (High)": 1.10, "Zone 5 (Cyclonic)": 1.18}
SEISMIC_ZONE_M = {"Zone 0 (Very Low)": 0.97, "Zone I": 1.00, "Zone II": 1.03, "Zone III": 1.06, "Zone IV": 1.10, "Zone V (High)": 1.16}
ROOF_M         = {"PEB + Insulated Panel": 1.00, "RCC Slab": 1.22, "Metal Deck + Insulation": 1.05}
COLUMN_M       = {"RCC": 1.12, "Steel": 1.00, "RCC+Steel": 1.18}
FUEL_M         = {"PNG": 1.00, "LPG": 1.08, "Diesel": 1.15, "Biomass": 0.92, "Electric": 1.28}
GRID_DG_ADD    = {"Excellent": 0.00, "Good": 0.02, "Average": 0.06, "Poor (frequent outages)": 0.12}
WATER_AVAIL_M  = {"Municipal": 0.85, "Municipal + Borewell": 1.00, "Borewell": 1.08, "Tanker": 1.20, "Recycled + Fresh": 1.10, "Limited": 1.25}
AMBIENT_HVAC_M = {"Tropical (25°C - 40°C)": 1.15, "Temperate (5°C - 30°C)": 1.00, "Cold (-10°C - 15°C)": 1.08, "Hot Arid (30°C - 48°C)": 1.20, "Cool Temperate (0°C - 22°C)": 1.05}
BUILDING_TYPE_M= {"RCC Industrial Building": 1.10, "Industrial Building (RCC + PEB)": 1.00, "Warehouse-PEB": 0.82}
PROJECT_TYPE_M = {"Greenfield": 1.00, "Brownfield / Expansion": 0.94}
INDUSTRY_TYPE_M= { "FMCG": 0.92}
TEMPERING_M    = {"Low": 0.94, "Medium": 1.00, "High": 1.10, "Very High": 1.22}
CONVEYOR_M     = {"Light": 0.94, "Standard": 1.00, "Heavy Duty": 1.15}

# ---------- Employee & Staff Facilities ----------
# ---------- Employee & Staff Facilities ----------
# ---------- Employee & Staff Facilities ----------

def calculate_employee_facilities(inp: ProjectInputs) -> Dict[str, Any]:
    admin_building_selected = "Admin Building" in (inp.building_components or [])

    employees = max(0, int(inp.num_employees or 0)) if admin_building_selected else 0
    male = max(0, int(inp.male_employees or 0)) if admin_building_selected else 0
    female = max(0, int(inp.female_employees or 0)) if admin_building_selected else 0

    clothing = str(inp.special_work_clothing or "Yes").strip().lower() == "yes"
    shoes = str(inp.work_shoes_required or "Yes").strip().lower() == "yes"
    canteen= str(inp.canteen_dining_required or "No").strip().lower() == "yes"
    country = str(inp.location_country or "").strip()


    if employees <= 0:
        return {
            "employees": 0, "male": 0, "female": 0, "lockers": 0,
            "changing_area_sqm": 0, "locker_area_sqm": 0,
            "shoe_storage_area_sqm": 0, "total_area_sqm": 0,
            "seating": 0, "street_shoe_storage_positions": 0,
            "work_shoe_storage_positions": 0, "items": [],
            "estimated_cost": 0, "cost_breakdown": {},
            "design_basis": ("Admin Building not selected"
                             if not admin_building_selected
                             else "No employees entered"
                             ),
            "facility_scope_status": (
                "Employee facilities excluded because Admin Building is not selected"
                if not admin_building_selected
                else "No employee facility scope generated"
                ),
            "locker_dimension_m": {"width": 0.30, "depth": 0.50},
            "locker_dimension_basis": "Germany ASR A4.1 reference module; verify local requirement",
            "shoe_storage_dimension_m": None, "shoe_storage_modules": 0,
            "shoe_storage_basis": "Not required", "changing_room_zones": 0,
            "changing_room_doors": 0, "privacy_partitions": 0,
            "facility_scope_status": "No employee facility scope generated",
            "wet_area_scope": "Not automatically assumed; no shower/wet-area input is provided",
            "fire_safety_scope": "Not applicable",
            "hvac_scope": "Not applicable",
        }

    lockers = employees

    # Individual locker module. Germany ASR A4.1 provides a 0.30 m x 0.50 m
    # reference locker footprint; other countries are treated as planning basis
    # unless a verified local dimensional requirement is available.
    locker_width_m = 0.30
    locker_depth_m = 0.50
    locker_area = lockers * locker_width_m * locker_depth_m
    locker_dimension_basis = (
        "Germany ASR A4.1 reference module"
        if country == "Germany"
        else "Planning module; verify local requirement"
    )

    # Changing-room movement area.
    # The rate is deliberately initialized before any country branching so
    # movement_area can never be undefined.
    movement_rate = 0.50
    rule_basis = "0.50 m²/user planning basis"

    if country == "Canada":
        movement_rate = 0.40
        rule_basis = "Canada regulatory benchmark: 0.40 m²/user"
    elif country == "Germany":
        movement_rate = 0.50
        rule_basis = "Germany ASR A4.1: 0.50 m²/user"

    movement_area = employees * movement_rate if clothing else 0.0
    changing_area = movement_area

    # Seating is required only when a dedicated changing room is provided.
    seating = math.ceil(employees / 4) if clothing else 0

    # Separate storage positions for street shoes and work shoes/boots.
    shoe_width_m = 0.30 if shoes else 0.0
    shoe_depth_m = 0.35 if shoes else 0.0
    shoe_storage_modules = 2 if shoes else 0
    shoe_storage_area = (
        employees * shoe_width_m * shoe_depth_m * shoe_storage_modules
    )
    shoe_storage_basis = (
        "Planning module; verify local requirement" if shoes else "Not required"
    )

    street_shoe_positions = employees if shoes else 0
    work_shoe_positions = employees if shoes else 0

    # The total facility area represents clear changing movement plus
    # locker and shoe-storage footprints. It does NOT enlarge the plant
    # footprint automatically; the facilities are located within the
    # Admin Building.
    total_area = changing_area + locker_area + shoe_storage_area

    # Country-specific employee-facility rates from rate_data.py.
    # These rates are now the explicit cost basis for the employee-facility scope.
    rates = get_employee_facility_rates(country)
    cost_civil_finish = round(total_area * rates["civil_finish"], 2)
    cost_mep = round(total_area * rates["mep"], 2)
    cost_lockers = round(employees * rates["locker"], 2)
    cost_shoe_storage = round((street_shoe_positions + work_shoe_positions) * rates["shoe_rack"], 2) if shoes else 0
    cost_benches = round(seating * rates["bench"], 2)
    estimated_cost = round(cost_civil_finish + cost_mep + cost_lockers + cost_shoe_storage + cost_benches, 2)
    cost_breakdown = {
        "civil_finish": cost_civil_finish, "mep_fitout": cost_mep,
        "locker_procurement": cost_lockers, "shoe_storage": cost_shoe_storage,
        "benches_seating": cost_benches, "total": estimated_cost,
        "rates_country": country,
        "rate_per_sqm_facility": round(estimated_cost / total_area, 2) if total_area > 0 else 0,
    }

    items = [
        {"item": "Individual Employee Lockers", "quantity": lockers, "unit": "No."},
        {"item": "Male Employee Lockers", "quantity": male, "unit": "No."},
        {"item": "Female Employee Lockers", "quantity": female, "unit": "No."},
        {"item": "Locker Storage Area", "quantity": round(locker_area, 2), "unit": "m²"},
        {"item": "Employee Facility Floor Finish", "quantity": round(total_area, 2), "unit": "m²"},
        {"item": "Employee Facility Ceiling Finish", "quantity": round(total_area, 2), "unit": "m²"},
        {"item": "Employee Facility Lighting", "quantity": round(total_area, 2), "unit": "m² planning area"},
        {"item": "Employee Facility Electrical", "quantity": round(total_area, 2), "unit": "m² planning area"},
    ]

    if shoes:
        items.extend([
            {"item": "Outside / Street Shoe Storage", "quantity": street_shoe_positions, "unit": "Employee positions"},
            {"item": "Non-Marking Work Shoe / Boot Storage", "quantity": work_shoe_positions, "unit": "Employee positions"},
            {"item": "Shoe Storage Planning Area", "quantity": round(shoe_storage_area, 2), "unit": "m²"},
        ])

    if clothing:
        male_room = 1 if male > 0 else 0
        female_room = 1 if female > 0 else 0
        changing_rooms = male_room + female_room
        doors = changing_rooms
        privacy_partitions = max(0, changing_rooms - 1)

        items.extend([
            {"item": "Changing Room Zones", "quantity": changing_rooms, "unit": "No."},
            {"item": "Changing Room Doors", "quantity": doors, "unit": "No."},
        ])

        if privacy_partitions:
            items.append({
                "item": "Privacy / Gender Separation Partition",
                "quantity": privacy_partitions,
                "unit": "No."
            })

        items.extend([
            {"item": "Mechanical / Natural Ventilation Scope", "quantity": round(total_area, 2), "unit": "m² served area"},
            {"item": "Emergency / General Lighting Scope", "quantity": round(total_area, 2), "unit": "m² served area"},
            {"item": "Electrical Power / Small-Power Scope", "quantity": round(total_area, 2), "unit": "m² served area"},
            {"item": "Fire & Life Safety Coordination", "quantity": 1, "unit": "LS"},
            {"item": "Emergency Egress / Access Coordination", "quantity": 1, "unit": "LS"},
            {"item": "Room Construction / Finishes Coordination", "quantity": 1, "unit": "LS"},
        ])

    return {
        "employees": employees,
        "male": male,
        "female": female,
        "lockers": lockers,
        "changing_area_sqm": round(changing_area, 2),
        "locker_area_sqm": round(locker_area, 2),
        "shoe_storage_area_sqm": round(shoe_storage_area, 2),
        "total_area_sqm": round(total_area, 2),
        "seating": seating,
        "street_shoe_storage_positions": street_shoe_positions,
        "work_shoe_storage_positions": work_shoe_positions,
        "estimated_cost": estimated_cost,
        "cost_breakdown": cost_breakdown,
        "locker_sections": 2 if clothing else 1,
        "locker_dimension_m": {
            "width": locker_width_m,
            "depth": locker_depth_m,
        },
        "locker_dimension_basis": locker_dimension_basis,
        "shoe_storage_dimension_m": (
            {"width": shoe_width_m, "depth": shoe_depth_m} if shoes else None
        ),
        "shoe_storage_modules": shoe_storage_modules,
        "shoe_storage_basis": shoe_storage_basis,
        "changing_room_zones": (
            (1 if male > 0 else 0) + (1 if female > 0 else 0)
            if clothing else 0
        ),
        "changing_room_doors": (
            (1 if male > 0 else 0) + (1 if female > 0 else 0)
            if clothing else 0
        ),
        "privacy_partitions": (
            max(
                0,
                ((1 if male > 0 else 0) + (1 if female > 0 else 0)) - 1
            )
            if clothing else 0
        ),
        "facility_location": "Admin Building",
        "design_basis": rule_basis,
        "facility_scope_status": (
            "Calculated planning scope; statutory requirements and detailed engineering govern final design"
        ),
        "wet_area_scope": (
            "Not automatically assumed; no shower/wet-area input is provided"
        ),
        "fire_safety_scope": (
            "Included as coordination scope; final equipment quantities require building/fire-code design"
        ),
        "hvac_scope": (
            "Area served reported; equipment capacity requires engineering design inputs"
        ),
        "items": items,
    }

# ---------- Canonical utility scope mapping ----------
# UI labels are mapped to the actual utility-system basket used for costing.
UTILITY_SCOPE_MAP = {
    "Boiler House": "Steam & Boiler System",
    "Steam Distribution": "Steam & Boiler System",
    "Chiller Plant": "Refrigeration / Cold Chain",
    "HVAC System": "HVAC",
    "Air Compressors": "Compressed Air System",
    "Process Piping": "Utility Piping",
    "Water Treatment Plant": "Water Supply System",
    "Fire Fighting System": "Fire Fighting System",
    "Electrical Substation": "Electrical Infrastructure",
    "DG Backup": "Electrical Infrastructure",
    "Solar Plant": "Electrical Infrastructure",
    "IT/OT System": "IT/OT System",
    "SCADA/MES": "IT/OT System",
    "Wastewater Treatment": "Wastewater Treatment",
    "WWTP": "Wastewater Treatment",
    "Steam & Boiler System": "Steam & Boiler System",
    "Refrigeration / Cold Chain": "Refrigeration / Cold Chain",
    "Compressed Air System": "Compressed Air System",
    "Water Supply System": "Water Supply System",
    "Electrical Infrastructure": "Electrical Infrastructure",
    "HVAC": "HVAC",
    "Utility Piping": "Utility Piping",
    "Fire Fighting System": "Fire Fighting System",
    "IT/OT System": "IT/OT System",
    "Wastewater Treatment": "Wastewater Treatment",
}

# ---------- Benchmark basket / scope allocation ----------
# The country factors in rate_data are calibrated at 1500 kg/m².
# The "others_pct" basket contains warehouse/ASRS, EPCM, statutory,
# safety/owner scope and the benchmark contingency. We separate those
# pieces so the user's contingency is applied exactly once.
BENCHMARK_CONTINGENCY_RATE = 0.048
OTHER_SCOPE_WEIGHTS = {
    "Warehouse / ASRS": 0.4045885097,
    "EPCM & Project Management": 0.2879718217,
    "Permits & Insurance / Statutory": 0.0173735066,
    "Safety & Working Dynamics": 0.1856347279,
    "External / Site Development": 0.1044314341,
}

# Product-specific utility intensity is applied to the utility basket,
# not to civil construction. Inputs supplied by the user further refine
# the applicable process systems.
PRODUCT_UTILITY_INTENSITY = {
    "Chocolate Plant": {
        "Refrigeration / Cold Chain": 1.20,
        "HVAC": 1.10,
        "Utility Piping": 1.08,
        "Steam & Boiler System": 1.05,
    },
    "Bakery + Chocolate Combo": {
        "Refrigeration / Cold Chain": 1.18,
        "HVAC": 1.10,
        "Utility Piping": 1.08,
        "Steam & Boiler System": 1.08,
    },
    "Bakery": {
        "Steam & Boiler System": 1.16,
        "Compressed Air System": 1.06,
        "HVAC": 1.08,
        "Refrigeration / Cold Chain": 0.92,
    },
    "Warehouse": {
        "Refrigeration / Cold Chain": 0.70,
        "HVAC": 0.65,
        "Steam & Boiler System": 0.60,
        "Compressed Air System": 0.70,
        "Utility Piping": 0.75,
    },
}

def _safe_factor(value: Any, default: float = 1.0) -> float:
    try:
        x = float(value)
        return x if math.isfinite(x) and x > 0 else default
    except Exception:
        return default

def _market_factor_set(inp: ProjectInputs) -> Dict[str, Any]:
    """Resolve country + city discipline factors without double-counting."""
    country = str(inp.location_country or "").strip()
    region = str(inp.region or "").strip()

    country_data = get_country_cost_factors(country)
    country_known = country in COUNTRY_COST_FACTORS

    # Region is used as the market-family fallback/validation layer.
    region_data = REGION_MULTIPLIERS.get(region, {})
    region_country = region_data.get(country)
    if not country_known and region_country is not None:
        # REGION_MULTIPLIERS may be a legacy scalar or a material/labour dict.
        if isinstance(region_country, dict):
            blended = (
                0.70 * _safe_factor(region_country.get("material"))
                + 0.30 * _safe_factor(region_country.get("labour"))
            )
        else:
            blended = _safe_factor(region_country)
        country_data = {
            "csa_factor": blended,
            "util_factor": blended,
            "others_pct": 0.60,
        }

    requested_city = city_factor_lookup(inp.location_city)
    benchmark_city = get_benchmark_city_factors(country)

    # City data are stored as raw indices. Divide by the country's
    # benchmark-city index so the benchmark city remains exactly 1.00.
    city_rel = {}
    for discipline in ("civil", "mechanical", "electrical", "labour"):
        req = _safe_factor(requested_city.get(discipline))
        bench = _safe_factor(benchmark_city.get(discipline))
        city_rel[discipline] = req / bench if bench else 1.0

    # Blend city material + labour separately by discipline.
    civil_city = 0.70 * city_rel["civil"] + 0.30 * city_rel["labour"]
    mech_city = 0.70 * city_rel["mechanical"] + 0.30 * city_rel["labour"]
    elec_city = 0.70 * city_rel["electrical"] + 0.30 * city_rel["labour"]

    return {
        "country": country,
        "region": region,
        "country_data": country_data,
        "country_known": country_known,
        "city_requested": requested_city,
        "city_benchmark": benchmark_city,
        "city_relative": city_rel,
        "civil_city": civil_city,
        "mechanical_city": mech_city,
        "electrical_city": elec_city,
    }

def _relative_structural_factor(inp: ProjectInputs) -> float:
    """Apply structural inputs as a ratio to the estimator's reference case."""
    def raw_factor(
        foundation_type, sbc, gwt, wind, seismic, column, roof_type, building_type,
        bay_spacing, wind_speed, far_fsi, num_floors, roof_types_by_floor
    ):
        foundation = FOUNDATION_M.get(foundation_type, 1.0)
        raw = (
            foundation
            * SBC_M.get(sbc, 1.0)
            * GWT_M.get(gwt, 1.0)
            * WIND_ZONE_M.get(wind, 1.0)
            * SEISMIC_ZONE_M.get(seismic, 1.0)
            * COLUMN_M.get(column, 1.0)
        )
        roof_m = ROOF_M.get(roof_type, 1.0)
        if roof_types_by_floor:
            vals = []
            for floor in range(max(1, num_floors)):
                roofs = roof_types_by_floor[floor] if floor < len(roof_types_by_floor) else [roof_type]
                roofs = roofs or [roof_type]
                vals.append(sum(ROOF_M.get(r, 1.0) for r in roofs) / len(roofs))
            roof_m = sum(vals) / len(vals)
        raw *= roof_m * BUILDING_TYPE_M.get(building_type, 1.0)
        raw *= (8.0 / max(2.0, bay_spacing)) ** 0.15
        raw *= 1.0 + max(0.0, (wind_speed - 24.0) * 0.008)
        raw *= 1.0 + max(0.0, (far_fsi - 1.5) * 0.06)
        return raw ** (1.0 / 2.5)

    requested = raw_factor(
        inp.foundation_type[0] if inp.foundation_type else "Raft Foundation",
        inp.sbc_soil_type, inp.gwt_depth, inp.wind_zone, inp.seismic_zone,
        inp.column_type, inp.roof_type, inp.building_type, inp.bay_spacing_m,
        inp.wind_speed_ms, inp.far_fsi, inp.num_floors, inp.roof_types_by_floor,
    )
    reference = raw_factor(
        "Raft Foundation", "Hard", "Medium (3-8 m)", "Zone 2",
        "Zone 0 (Very Low)", "Steel", "PEB + Insulated Panel",
        "Industrial Building (RCC + PEB)", 8.0, 24.0, 1.2, 1,
        [["PEB + Insulated Panel"]],
    )
    return max(0.50, min(1.80, requested / reference if reference else 1.0))

def _relative_complexity_factor(inp: ProjectInputs) -> Tuple[float, List[str]]:
    raw = 1.0
    active = []
    for key, enabled in (inp.complexity or {}).items():
        if enabled and key in COMPLEXITY_FACTORS:
            raw *= COMPLEXITY_FACTORS[key]
            active.append(key)
    # The benchmark includes GMP + N+1, so only the delta from that
    # benchmark is applied to avoid compounding the same conditions twice.
    rel = raw / BENCHMARK_COMPLEXITY_M
    return max(0.60, min(1.80, rel)), active

def _product_utility_multiplier(inp: ProjectInputs, system_name: str) -> float:
    product = str(inp.product_category or "")
    base = PRODUCT_UTILITY_INTENSITY.get(product, {}).get(system_name, 1.0)

    # Preserve the existing user-provided process sizing inputs as secondary
    # engineering modifiers for the systems they actually affect.
    if "chocolate" in product.lower() or "combo" in product.lower():
        if system_name == "Refrigeration / Cold Chain":
            base *= 1.0 + max(0.0, inp.cooling_tunnel_load_tr - 180.0) / 1800.0
        elif system_name == "HVAC":
            base *= 1.0 + max(0.0, inp.humidity_controlled_pct - 40.0) / 1000.0
        elif system_name == "Steam & Boiler System":
            base *= 1.0 + max(0.0, inp.process_hot_water_lph - 2500.0) / 50000.0
    if any(t in product.lower() for t in ("biscuit", "bakery", "wafer", "cookie")):
        if system_name == "Steam & Boiler System":
            base *= 1.0 + max(0.0, inp.oven_capacity_kg_hr - 1200.0) / 20000.0
        elif system_name == "Compressed Air System":
            base *= 1.0 + max(0.0, inp.compressed_air_demand_cfm - 1500.0) / 15000.0
    return max(0.50, min(2.50, base))

def _system_scope_enabled(inp: ProjectInputs, canonical_name: str) -> bool:
    selected = {
        UTILITY_SCOPE_MAP[label]
        for label in (inp.utility_scope or [])
        if label in UTILITY_SCOPE_MAP
    }
    product = str(inp.product_category or "").lower()
    # Food manufacturing baseline: the benchmark basket includes the core
    # utility/process systems. The UI selection can add optional systems,
    # but it must not silently remove core scope from a food plant.
    if product in {"chocolate plant","bakery", "bakery + chocolate combo"}:
        return True
    if product == "warehouse":
        core = {
            "Electrical Infrastructure",
            "Fire Fighting System",
            "Water Supply System",
            "HVAC",
            "IT/OT System",
        }
        return canonical_name in (core | selected)
    return canonical_name in selected

def compute_estimate(inp: ProjectInputs, live_index: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    built_up = inp.length_m * inp.width_m * max(1, inp.num_floors)
    employee_facilities = calculate_employee_facilities(inp)

    market = _market_factor_set(inp)
    country_data = market["country_data"]

    # Automatic product -> floor-load assignment.
    floor_load_info = get_floor_load_multiplier(
        product_category=inp.product_category,
        country=inp.location_country,
    )
    floor_load_m = _safe_factor(floor_load_info.get("multiplier"))

    # Location tier is an explicit project-location adjustment.
    tier_m = _safe_factor(LOCATION_FACTOR.get(inp.location_tier, 1.0))

    # Engineering factors are normalized to the benchmark scenario rather
    # than compounded on top of an already benchmarked country rate.
    structural_rel = _relative_structural_factor(inp)
    complexity_rel, active_complexity = _relative_complexity_factor(inp)
    project_type_rel = 1.0 if inp.project_type == "Greenfield" else _safe_factor(PROJECT_TYPE_M.get(inp.project_type, 1.0))
    industry_rel = 1.0

    # Live commodity index is allowed to move the material-heavy portions,
    # but is deliberately capped to prevent a proxy index from dominating.
    live_m = max(0.85, min(1.15, _safe_factor((live_index or {}).get("material_index", 1.0))))
    # Live commodity index is reporting-only; the company benchmark is already normalized.
    cost_live_m = 1.0

    csa_factor = _safe_factor(country_data.get("csa_factor"))
    util_factor = _safe_factor(country_data.get("util_factor"))
    others_pct = max(0.0, float(country_data.get("others_pct", 0.60)))

    civil_market_m = market["civil_city"]
    mech_market_m = market["mechanical_city"]
    elec_market_m = market["electrical_city"]

    # ---------------- Direct CSA basket ----------------
    csa_base = USA_BASE_CSA * csa_factor
    csa_m = (
        floor_load_m
        * civil_market_m
        * structural_rel
        * complexity_rel
        * tier_m
        * project_type_rel
        * cost_live_m
    )
    csa_total = round(csa_base * built_up * csa_m, 2)

    # Allocate the direct CSA basket across the existing civil activities.
    civil_weights = {
        "Excavation": 0.055,
        "PCC (M10)": 0.025,
        "RCC Foundation (Raft)": 0.135,
        "Structural Steel (PEB)": 0.245,
        "RCC Superstructure": 0.150,
        "Roofing (Insulated Panel)": 0.075,
        "Flooring (Epoxy + PU)": 0.105,
        "Walls (Block + Plaster + Tile)": 0.115,
        "Plumbing & Sanitary": 0.095,
    }
    civil_scope_names = [name for name, *_ in CIVIL_ACTIVITIES if name in civil_weights]
    weight_sum = sum(civil_weights[n] for n in civil_scope_names) or 1.0
    boq_rows: List[Dict[str, Any]] = []
    building_total = 0.0
    for activity, unit, _, category in CIVIL_ACTIVITIES:
        if activity not in civil_weights:
            continue
        amount = round(csa_total * civil_weights[activity] / weight_sum, 2)
        building_total += amount
        boq_rows.append({
            "activity": activity,
            "unit": unit,
            "quantity": 1,
            "rate": amount,
            "amount": amount,
            "category": category,
            "cost_basis": "Country CSA basket × city × floor-load × engineering factors",
        })

    building_total = round(building_total, 2)

    # ---------------- Utility basket ----------------
    # Country utility benchmark is allocated by discipline-specific city factors.
    utility_city_weight = (
        0.35 * mech_market_m
        + 0.35 * elec_market_m
        + 0.30 * market["civil_city"]
    )
    grid_reference = 1.0 + GRID_DG_ADD.get("Good", 0.0)
    grid_requested = 1.0 + GRID_DG_ADD.get(inp.grid_reliability, 0.0)
    utility_environment_m = (
        _safe_factor(FUEL_M.get(inp.fuel_type, 1.0))
        * _safe_factor(WATER_AVAIL_M.get(inp.water_availability, 1.0))
        * (
            _safe_factor(AMBIENT_HVAC_M.get(inp.ambient_temp_range, 1.0))
            / _safe_factor(AMBIENT_HVAC_M.get("Temperate (5°C - 30°C)", 1.0))
        ) ** 0.35
        * (grid_requested / grid_reference)
        * (1.0 + max(0.0, inp.relative_humidity_pct - 70.0) * 0.0025)
    )
    utility_environment_m = max(0.65, min(1.60, utility_environment_m))

    util_base = USA_BASE_UTIL * util_factor
    utility_rows = []
    utilities_total = 0.0

    product_key = str(inp.product_category or "")
    preset = INDUSTRY_PRESETS.get(product_key,{"utilities_pct": 0.50})
    # Chocolate is the reference food-process utility intensity (0.63).
    # Other categories therefore scale the complete utility basket without
    # changing the country/city market basis.
    product_total_m = max(0.35, min(1.35, float(preset.get("utilities_pct", 0.50)) / 0.63))

    selected_systems = {
        name for name in UTILITY_SYSTEM_WEIGHTS
        if _system_scope_enabled(inp, name)
    }

    if selected_systems:
        raw_product = {
            name: _product_utility_multiplier(inp, name)
            for name in selected_systems
        }
        weighted_raw = sum(
            UTILITY_SYSTEM_WEIGHTS[name][0] * raw_product[name]
            for name in selected_systems
        )
        selected_weight = sum(
            UTILITY_SYSTEM_WEIGHTS[name][0]
            for name in selected_systems
        )
        product_normalizer = weighted_raw / selected_weight if selected_weight else 1.0

        for name, (weight, discipline, description) in UTILITY_SYSTEM_WEIGHTS.items():
            if name not in selected_systems:
                continue

            discipline_m = {
                "mechanical": mech_market_m,
                "electrical": elec_market_m,
                "civil": market["civil_city"],
            }.get(discipline, mech_market_m)

            raw_product_m = raw_product[name]
            product_m = raw_product_m / product_normalizer if product_normalizer else 1.0

            amount = (
                util_base
                * built_up
                * weight
                * product_total_m
                * discipline_m
                * utility_environment_m
                * product_m
                * tier_m
                * project_type_rel
                * complexity_rel
                * cost_live_m
            )
            amount = round(amount, 2)
            utilities_total += amount
            utility_rows.append({
                "name": name,
                "unit": "LS",
                "amount": amount,
                "discipline": discipline,
                "description": description,
                "country_factor": round(util_factor, 4),
                "city_factor": round(discipline_m, 4),
                "product_factor": round(product_total_m * product_m, 4),
            })

    utilities_total = round(utilities_total, 2)
    if utilities_total > 0:
        boq_rows.append({
            "activity": "Utilities & Process Systems",
            "unit": "LS",
            "quantity": 1,
            "rate": utilities_total,
            "amount": utilities_total,
            "category": "Utilities",
            "scope": utility_rows,
            "cost_basis": "Country utility basket × discipline city factors × product/process factors",
        })

    # ---------------- Non-direct project basket ----------------
    # Split the country 'others' pool into explicit project scopes, removing
    # the embedded benchmark contingency first.
    direct_total = csa_total + utilities_total
    benchmark_other_pool = direct_total * others_pct
    precont_other = max(
        0.0,
        (benchmark_other_pool - BENCHMARK_CONTINGENCY_RATE * direct_total)
        / (1.0 + BENCHMARK_CONTINGENCY_RATE),
    )

    scope_flags = {
        "Warehouse / ASRS": "Warehouse" in (inp.building_components or []) or inp.product_category == "Warehouse",
        "External / Site Development": bool(inp.include_roads or inp.include_landscaping or inp.include_fence),
        "EPCM & Project Management": True,
        "Permits & Insurance / Statutory": True,
        "Safety & Working Dynamics": True,
    }

    active_weights = {
        k: w for k, w in OTHER_SCOPE_WEIGHTS.items() if scope_flags.get(k, True)
    }
    weight_total = sum(active_weights.values()) or 1.0

    
    other_rows = []
    other_total = 0.0

    for name, weight in active_weights.items():
        amount = round(precont_other * weight / weight_total, 2)

        # Replace the combined external scope with individual activities.
        if name == "External / Site Development":
            external_items = []

            if inp.include_roads:
                external_items.append({
                    "activity": "Roads, Pathways & Parking",
                    "unit": "m2",
                    "quantity": max(0.0, float(inp.land_area_sqm) * 0.30),
                    "category": "Infra",
                })

            if inp.include_fence:
                external_items.append({
                    "activity": "Compound Wall / Fence",
                    "unit": "m",
                    "quantity": max(
                        0.0,
                        4 * (float(inp.land_area_sqm) ** 0.5),
                    ),
                    "category": "Infra",
                })

            if inp.include_landscaping:
                external_items.append({
                    "activity": "Landscaping",
                    "unit": "m2",
                    "quantity": max(0.0, float(inp.land_area_sqm) * 0.15),
                    "category": "Infra",
                })

            total_quantity = sum(item["quantity"] for item in external_items)

            for item in external_items:
                # Allocate the existing external-scope amount across
                # enabled activities in proportion to their quantities.
                share = (
                    item["quantity"] / total_quantity
                    if total_quantity > 0
                    else 0
                )
                item_amount = round(amount * share, 2)

                other_rows.append({
                    **item,
                    "quantity": round(item["quantity"], 2),
                    "rate": (
                        round(item_amount / item["quantity"], 2)
                        if item["quantity"] > 0
                        else 0
                    ),
                    "amount": item_amount,
                    "cost_basis": (
                        "Allocated share of existing external/site "
                        "development estimate; quantity is indicative"
                    ),
                })

            # Preserve the original external amount in the project total.
            other_total += amount
            continue

        other_total += amount
        other_rows.append({
            "activity": name,
            "unit": "LS",
            "quantity": 1,
            "rate": amount,
            "amount": amount,
            "category": "Project Indirect / Scope",
        })


    # Employee facilities are an explicit additional scope driven by employee count.
    employee_facility_cost = round(employee_facilities.get("estimated_cost", 0), 2)
    if employee_facility_cost > 0:
        other_rows.append({
            "activity": "Employee & Staff Facilities",
            "unit": "LS",
            "quantity": 1,
            "rate": employee_facility_cost,
            "amount": employee_facility_cost,
            "category": "Employee Facilities",
            "scope": employee_facilities["items"],
            "employees": employee_facilities["employees"],
            "lockers": employee_facilities["lockers"],
            "area_sqm": employee_facilities["total_area_sqm"],
            "cost_status": "Costed from country-specific employee facility rates",
        })

    for row in other_rows:
        boq_rows.append(row)

    other_total = round(other_total, 2)

    # User contingency is applied exactly once, after all pre-contingency scope.
    pre_contingency_subtotal = round(
        building_total + utilities_total + other_total + employee_facility_cost,
        2,
    )
    contingency = round(pre_contingency_subtotal * max(0.0, inp.contingency_pct) / 100.0, 2)
    total = round(pre_contingency_subtotal + contingency, 2)

    boq_rows.append({
        "activity": "Contingency",
        "unit": "LS",
        "quantity": 1,
        "rate": contingency,
        "amount": contingency,
        "category": "Contingency",
    })

    # Keep a separate external total for UI compatibility.
    external_total = round(
        sum(r["amount"] for r in other_rows if r["activity"] == "External / Site Development"),
        2,
    )

    confidence = 88
    if not market["country_known"]:
        confidence -= 10
    if not market["city_requested"].get("matched", False):
        confidence -= 4
    if inp.project_type != "Greenfield":
        confidence -= 5
    if inp.location_tier == "Remote":
        confidence -= 4
    if (live_index or {}).get("source") == "fallback":
        confidence -= 1
    confidence = max(45, min(96, confidence))
    conf_label = "High" if confidence >= 85 else "Medium" if confidence >= 70 else "Low"

    def pct(x):
        return round((x / total) * 100, 2) if total > 0 else 0

    def cost_per_sqm(x):
        return round(x / built_up, 2) if built_up > 0 else 0

    breakdown = [
        {"name": "Civil / CSA", "value": building_total, "cost_per_sqm": cost_per_sqm(building_total), "pct": pct(building_total)},
        {"name": "Utilities & Process", "value": utilities_total, "cost_per_sqm": cost_per_sqm(utilities_total), "pct": pct(utilities_total)},
        {"name": "External / Site Development", "value": external_total, "cost_per_sqm": cost_per_sqm(external_total), "pct": pct(external_total)},
        {"name": "EPCM & Project Management", "value": round(sum(r["amount"] for r in other_rows if r["activity"] == "EPCM & Project Management"), 2), "cost_per_sqm": cost_per_sqm(sum(r["amount"] for r in other_rows if r["activity"] == "EPCM & Project Management")), "pct": pct(sum(r["amount"] for r in other_rows if r["activity"] == "EPCM & Project Management"))},
        {"name": "Permits & Insurance / Statutory", "value": round(sum(r["amount"] for r in other_rows if r["activity"] == "Permits & Insurance / Statutory"), 2), "cost_per_sqm": cost_per_sqm(sum(r["amount"] for r in other_rows if r["activity"] == "Permits & Insurance / Statutory")), "pct": pct(sum(r["amount"] for r in other_rows if r["activity"] == "Permits & Insurance / Statutory"))},
        {"name": "Safety & Working Dynamics", "value": round(sum(r["amount"] for r in other_rows if r["activity"] == "Safety & Working Dynamics"), 2), "cost_per_sqm": cost_per_sqm(sum(r["amount"] for r in other_rows if r["activity"] == "Safety & Working Dynamics")), "pct": pct(sum(r["amount"] for r in other_rows if r["activity"] == "Safety & Working Dynamics"))},
        {"name": "Warehouse / ASRS", "value": round(sum(r["amount"] for r in other_rows if r["activity"] == "Warehouse / ASRS"), 2), "cost_per_sqm": cost_per_sqm(sum(r["amount"] for r in other_rows if r["activity"] == "Warehouse / ASRS")), "pct": pct(sum(r["amount"] for r in other_rows if r["activity"] == "Warehouse / ASRS"))},
        {"name": "Employee & Staff Facilities", "value": employee_facility_cost, "cost_per_sqm": cost_per_sqm(employee_facility_cost), "pct": pct(employee_facility_cost)},
        {"name": "Contingency", "value": contingency, "cost_per_sqm": cost_per_sqm(contingency), "pct": pct(contingency)},
    ]

    sorted_boq = sorted(boq_rows, key=lambda r: r["amount"], reverse=True)
    top12 = []
    for i, row in enumerate(sorted_boq[:12], start=1):
        r2 = dict(row)
        r2["rank"] = i
        r2["pct_of_total"] = round((row["amount"] / total) * 100, 2) if total > 0 else 0
        top12.append(r2)

    duration = round(8 + built_up / 6000 + (0.15 * inp.num_floors), 1)
    cap = inp.production_capacity_tpd
    is_chocolate = "chocolate" in (inp.product_category or "").lower() or "combo" in (inp.product_category or "").lower()
    is_biscuit = any(t in (inp.product_category or "").lower() for t in ["biscuit", "bakery", "wafer", "cookie"])

    utility_demand = {
        "water_kld": round(max(20, 0.30 * cap * 10), 0),
        "steam_kg_hr": round(
            1800 if is_chocolate else
            2200 if is_biscuit else
            max(1200, cap * 15), 0
        ),
        "chiller_tr": round(inp.cooling_tunnel_load_tr, 0),
        "power_kva": round(max(500, cap * 12), 0),
        "compressed_air_cfm": round(inp.compressed_air_demand_cfm, 0),
        "etp_kld": round(max(30, cap * 1.2), 0),
        "fire_water_m3": 600,
    }

    n = max(6, min(24, int(round(duration))))
    trend = []
    start = datetime.now(timezone.utc)
    cum = 0.0
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

    # Overall market delta is shown for transparency only; it is not used as
    # a second global multiplier.
    benchmark_direct = USA_BASE_CSA + USA_BASE_UTIL
    market_direct_psm = (USA_BASE_CSA * csa_factor) + (USA_BASE_UTIL * util_factor)
    market_delta = round((market_direct_psm / benchmark_direct - 1.0) * 100.0, 1)

    return {
        "employee_facilities": employee_facilities,
        "totals": {
            "total_project_cost": total,
            "cost_per_sqm": round(total / built_up, 2) if built_up else 0,
            "cost_per_mt": round(total / inp.annual_output_mt, 2) if inp.annual_output_mt else 0,
            "duration_months": duration,
            "confidence_score": confidence,
            "confidence_label": conf_label,
            "contingency": contingency,
            "contingency_pct": inp.contingency_pct,
            "region_benchmark_delta_pct": market_delta,
            "built_up_area_sqm": round(built_up, 2),
            "employee_facility_area_sqm": round(employee_facilities["total_area_sqm"], 2),
            "employee_lockers": employee_facilities["lockers"],
            "employee_seating": employee_facilities["seating"],
            "employee_shoe_storage_positions": employee_facilities["street_shoe_storage_positions"] + employee_facilities["work_shoe_storage_positions"],
            "employee_facility_cost": employee_facility_cost,
        },
        "breakdown": breakdown,
        "employee_facilities": employee_facilities,
        "boq": sorted_boq,
        "top_cost_items": top12,
        "utilities": utility_rows,
        "utilities_total": utilities_total,
        "utility_demand": utility_demand,
        "cost_trend": trend,
        "multipliers": {
            "region": 1.0,
            "tier": round(tier_m, 4),
            "complexity": round(complexity_rel, 4),
            "building": round(structural_rel, 4),
            "utility": round(utility_environment_m, 4),
            "project_type": round(project_type_rel, 4),
            "live_material_index": round(live_m, 4),
            "floor_load": round(floor_load_m, 4),
            "floor_load_info": floor_load_info,
            "building_components_scope": 1.0,
            "combined": round(
                floor_load_m * structural_rel * complexity_rel * tier_m * project_type_rel,
                4,
            ),
            "roof_types_by_floor": inp.roof_types_by_floor,
        },
        "market_factors": {
            "cost_method": "Country benchmark basket + normalized city adjustment + product/floor-load scope drivers",
            "region": market["region"],
            "country": market["country"],
            "country_known": market["country_known"],
            "csa_factor": round(csa_factor, 4),
            "util_factor": round(util_factor, 4),
            "others_pct": round(others_pct, 4),
            "city_requested": market["city_requested"].get("resolved"),
            "city_benchmark": market["city_benchmark"].get("resolved") if isinstance(market["city_benchmark"], dict) else None,
            "city_relative": {k: round(v, 4) for k, v in market["city_relative"].items()},
            "civil_effective": round(civil_market_m, 4),
            "mechanical_effective": round(mech_market_m, 4),
            "electrical_effective": round(elec_market_m, 4),
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
        m = re.search(r"{[\s\S]*}", text)
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
        "regions": {region: list(countries.keys()) for region, countries in REGION_MULTIPLIERS.items()},        # Stage 2 - Region
        "tiers": list(LOCATION_FACTOR.keys()),              # Stage 1 - Country tier
        # ---- Step 1: Project Identification ----
        "project_types": ["Greenfield", "Brownfield / Expansion"],
        "industries": ["FMCG"],
        "product_categories": list(INDUSTRY_PRESETS.keys()),
        "product_category_load": PRODUCT_CATEGORY_LOAD,
        # ---- Step 2: Building Geometry ----
        "building_types": [
             "RCC Industrial Building", "Industrial Building (RCC + PEB)",
            "Warehouse-PEB",
        ],
        "building_components": [
            "Admin Building","RM Warehouse","Production Floor","WH-Bakery","WH-Chocolate","Utilities Block","Territory Packaging Hall","R&D Center",
        ],
        # ---- Step 3: Structural & Site ----
        "foundation_types": [
            "Isolated Footing", "Raft Foundation","Pile Foundation",
            "Engineering Fill",
        ],
        "sbc_soil_types": [
            "Hard","Soft",
        ],
        "roof_types": ["PEB + Insulated Panel", "RCC Slab", "Metal Deck + Insulation"],
        "column_types": ["RCC", "Steel", "RCC+Steel"],
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
            "WTP", "Nitrogen/CO2 Plant", "Fire Fighting System",
            "Electrical Substation", "DG Backup", "Solar Plant",
            "Steam Distribution", "Process Piping", "IT/OT System", "SCADA/MES",
             "WWTP",
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
            {"key": "brownfield", "label": "Brownfield Tie-ins"},
            {"key": "explosion_risk", "label": "Explosion Risk / Dust Areas"},
            {"key": "utility_redundancy", "label": "Utility Redundancy (N+1)"},
            {"key": "remote_site", "label": "Remote Site"},
        ],
        "currencies": list(CURRENCY_SYMBOLS.keys()),
        "cities": sorted({k.title() for k in CITY_FACTORS.keys()}),
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




@api_router.get("/estimator/location-lookup")
async def location_lookup(city: str):
    import logging

    city = city.strip()

    if len(city) < 2:
        raise HTTPException(
            status_code=400,
            detail="Please enter a valid city name."
        )

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": city,
                    "format": "jsonv2",
                    "addressdetails": 1,
                    "limit": 5,
                },
                headers={
                    "User-Agent": "ConstructionEstimator/1.0 (location lookup)"
                },
            )

            if response.status_code == 429:
                logging.warning(
                    "OpenStreetMap rate limit reached for city: %s",
                    city
                )
                raise HTTPException(
                    status_code=503,
                    detail=(
                        "The location service is temporarily busy. "
                        "Please wait a minute and try again."
                    )
                )

            response.raise_for_status()
            results = response.json()

    except HTTPException:
        raise
    except httpx.HTTPError:
        logging.exception("Location lookup request failed")
        raise HTTPException(
            status_code=502,
            detail="Could not contact the location service. Please try again."
        )

    locations = []
    seen = set()

    for item in results:
        address = item.get("address", {})
        country = address.get("country")

        if not country:
            continue

        city_name = (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or address.get("municipality")
            or city
        )

        country_code = address.get("country_code", "").upper()

        key = (city_name.casefold(), country.casefold())
        if key in seen:
            continue
        seen.add(key)

        matched_region = next(
            (
                region_name
                for region_name, countries in REGION_MULTIPLIERS.items()
                if any(
                    str(mapped_country).casefold() == country.casefold()
                    for mapped_country in countries
                )
            ),
            None,
        )

        locations.append({
            "city": city_name,
            "state": (
                address.get("state")
                or address.get("province")
                or address.get("region")
                or ""
            ),
            "country": country,
            "country_code": country_code,
            "region": matched_region,
            "formatted": item.get("display_name", ""),
        })

    if not locations:
        raise HTTPException(
            status_code=404,
            detail="No matching location found. Try entering the city and country."
        )

    return {"locations": locations}




@api_router.get("/estimator/{est_id}")
async def get_estimate(est_id: str):
    doc = await db.estimates.find_one({"id": est_id}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "not found")
    return doc


app.include_router(api_router)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

    
