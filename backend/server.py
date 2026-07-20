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
    # Step 1
    project_name: str = "Chocolate & Bakery Manufacturing Plant"
    project_type: str = "Greenfield"           # Greenfield / Brownfield / Retrofit
    industry_type: str = "Chocolate Plant"
    location_city: str = "Hamburg"
    location_country: str = "Germany"
    region: str = "Europe"
    location_tier: str = "Metro"                # Metro / Non-Metro / Remote
    # Step 2 - geometry
    building_type: str = "Industrial Building (RCC + PEB)"
    length_m: float = 185.0
    width_m: float = 100.0
    height_m: float = 10.5
    num_floors: int = 1
    bay_spacing_m: float = 8.0
    plot_area_sqm: float = 32000.0
    # Step 3 - structural
    soil_type: str = "Medium Dense Sand"
    foundation_type: str = "Raft Foundation"
    floor_load_kn: float = 5.0
    column_type: str = "Steel"
    roof_type: str = "PEB + Insulated Panel"
    seismic_zone: str = "Zone 0 (Very Low)"
    wind_speed_ms: float = 24.0
    # Step 4 - utilities
    utility_scope: List[str] = Field(default_factory=lambda: [
        "Boiler House", "Chiller Plant", "HVAC System", "Air Compressors",
        "Water Treatment Plant", "Fire Fighting System", "Electrical Substation",
    ])
    production_capacity_tpd: float = 120.0
    annual_output_mt: float = 36000.0
    # Step 5 - infra
    include_roads: bool = True
    include_landscaping: bool = True
    include_fence: bool = True
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


# ---------- Core estimator ----------
def compute_estimate(inp: ProjectInputs) -> Dict[str, Any]:
    built_up = inp.length_m * inp.width_m * inp.num_floors  # m² gross floor
    plot_area = inp.plot_area_sqm

    region_m = REGION_MULTIPLIERS.get(inp.region, 1.0)
    tier_m = LOCATION_FACTOR.get(inp.location_tier, 1.0)

    # Complexity multiplier (compound)
    complexity_m = 1.0
    active_complexity = []
    for k, v in inp.complexity.items():
        if v and k in COMPLEXITY_FACTORS:
            complexity_m *= COMPLEXITY_FACTORS[k]
            active_complexity.append(k)

    global_m = region_m * tier_m * complexity_m

    # Auto quantity take-off (heuristic ratios) - proportional to built-up area
    a = built_up
    perimeter = 2 * (inp.length_m + inp.width_m)
    boq_rows: List[Dict[str, Any]] = []

    qty_map = {
        "Excavation":                     a * 0.65,   # m³
        "PCC (M10)":                      a * 0.10,   # m³
        "RCC Foundation (Raft)":          a * 0.42,   # m³
        "Structural Steel (PEB)":         a * 0.055,  # MT
        "RCC Superstructure":             a * 0.24 * (inp.num_floors - 1 if inp.num_floors > 1 else 0.15),
        "Roofing (Insulated Panel)":      a,          # m²
        "Flooring (Epoxy + PU)":          a,          # m²
        "Walls (Block + Plaster + Tile)": perimeter * inp.height_m * inp.num_floors,
        "Plumbing & Sanitary":            1,
        "External Works & Roads":         plot_area * 0.28 if inp.include_roads else 0,
        "Compound Wall / Fence":          (perimeter + 200) if inp.include_fence else 0,
        "Landscaping":                    plot_area * 0.15 if inp.include_landscaping else 0,
    }

    building_total = 0.0
    for activity, unit, base_rate, category in CIVIL_ACTIVITIES:
        qty = round(qty_map.get(activity, 0), 2)
        rate = round(base_rate * global_m, 2)
        amount = round(qty * rate, 2)
        if amount > 0:
            boq_rows.append({
                "activity": activity, "unit": unit, "quantity": qty,
                "rate": rate, "amount": amount, "category": category,
            })
            building_total += amount

    # Utilities cost (scope-filtered)
    utilities_total = 0.0
    utilities_rows = []
    for name, unit, base_rate in UTILITY_SYSTEMS:
        # Match utility to scope tags
        included = False
        s = name.lower()
        for scope in inp.utility_scope:
            if scope.lower() in s or s.split()[0] in scope.lower():
                included = True
                break
        if not included and name in ("Water Supply System", "Electrical Infrastructure", "Fire Fighting System"):
            included = True  # base essentials always in
        if included:
            # Scale utility by capacity vs 100 TPD baseline
            cap_scale = max(0.5, (inp.production_capacity_tpd / 100.0))
            amount = round(base_rate * global_m * cap_scale, 2)
            utilities_rows.append({
                "name": name, "unit": unit, "amount": amount,
            })
            utilities_total += amount

    # Add utilities as a BOQ line
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
    other_fees = round(subtotal * 0.06, 2)  # design + PM + insurance
    boq_rows.append({
        "activity": "Design + PM + Other Fees", "unit": "LS", "quantity": 1,
        "rate": other_fees, "amount": other_fees, "category": "Other",
    })

    subtotal += other_fees
    contingency = round(subtotal * (inp.contingency_pct / 100.0), 2)
    total = subtotal + contingency

    # Confidence score (0-100)
    # base 92 - penalize for uncertainty flags
    confidence = 92
    if inp.project_type == "Brownfield":
        confidence -= 6
    if inp.location_tier == "Remote":
        confidence -= 4
    if inp.complexity.get("brownfield"): confidence -= 3
    if inp.complexity.get("explosion_risk"): confidence -= 3
    if inp.complexity.get("remote_site"): confidence -= 2
    if inp.production_capacity_tpd == 0:
        confidence -= 8
    confidence = max(45, min(96, confidence))
    conf_label = "High" if confidence >= 85 else "Medium" if confidence >= 70 else "Low"

    # % breakdown
    def pct(x): return round((x / total) * 100, 2) if total > 0 else 0
    breakdown = [
        {"name": "Civil Building", "value": round(building_total, 2), "pct": pct(building_total)},
        {"name": "Utilities & Process", "value": round(utilities_total, 2), "pct": pct(utilities_total)},
        {"name": "Infra & External", "value": infra_total, "pct": pct(infra_total)},
        {"name": "Compliance (GMP)", "value": compliance_total, "pct": pct(compliance_total)},
        {"name": "Other & Fees", "value": other_fees, "pct": pct(other_fees)},
        {"name": "Contingency", "value": contingency, "pct": pct(contingency)},
    ]

    # Top 12 cost items sorted by amount
    sorted_boq = sorted(boq_rows, key=lambda r: r["amount"], reverse=True)
    top12 = []
    for i, r in enumerate(sorted_boq[:12], start=1):
        r2 = dict(r)
        r2["rank"] = i
        r2["pct_of_total"] = round((r["amount"] / total) * 100, 2) if total > 0 else 0
        top12.append(r2)

    # Duration (heuristic): 8 + area/6000 months
    duration = round(8 + built_up / 6000 + (0.15 * inp.num_floors), 1)

    # Utility demand cards
    cap = inp.production_capacity_tpd
    utility_demand = {
        "water_kld": round(0.35 * cap * 10 + 20, 0),
        "steam_kg_hr": round(35 * cap + 400, 0),
        "chiller_tr": round(3.5 * cap, 0),
        "power_kva": round(23 * cap + 300, 0),
        "compressed_air_cfm": round(12 * cap + 300, 0),
        "etp_kld": round(1.5 * cap, 0),
        "fire_water_m3": 600,
    }

    # 12-month cost trend (S-curve)
    n = int(round(duration))
    n = max(6, min(24, n))
    import math
    trend = []
    start = datetime.now(timezone.utc)
    cum = 0
    for i in range(n):
        # S-curve weight
        x = (i + 1) / n
        # cumulative pct
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
            "region": region_m, "tier": tier_m, "complexity": round(complexity_m, 4),
            "combined": round(global_m, 4),
        },
        "active_complexity": active_complexity,
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
    """Return dropdown / static reference data for the wizard."""
    return {
        "regions": list(REGION_MULTIPLIERS.keys()),
        "tiers": list(LOCATION_FACTOR.keys()),
        "industries": list(INDUSTRY_PRESETS.keys()),
        "project_types": ["Greenfield", "Brownfield / Expansion", "Retrofit / Capacity Upgrade"],
        "building_types": [
            "Industrial Shed", "RCC Industrial Building", "Industrial Building (RCC + PEB)",
            "Warehouse", "Utility / Admin Block", "Mezzanine", "Hybrid",
        ],
        "foundation_types": [
            "Isolated Footing", "Combined Footing", "Raft Foundation",
            "Pile Foundation", "Engineering Fill",
        ],
        "soil_types": [
            "Black Cotton", "Silty", "Reclaimed / Engineering Fill",
            "Hard Stone", "Medium Dense Sand",
        ],
        "roof_types": ["PEB + Insulated Panel", "RCC Slab", "Metal Deck + Insulation"],
        "column_types": ["RCC", "Steel", "Composite"],
        "utility_scope": [s for s, _, _ in UTILITY_SYSTEMS] + [
            "Boiler House", "Chiller Plant", "HVAC System", "Air Compressors",
            "Water Treatment Plant", "Nitrogen Plant", "Electrical Substation",
            "DG Backup", "Solar Plant", "Steam Distribution", "Process Piping",
        ],
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


@api_router.post("/estimator/calculate")
async def calculate(inp: ProjectInputs):
    result = compute_estimate(inp)
    ai = await generate_ai_insights(inp, result)
    result["insights"] = ai
    fx = await get_fx_rates()
    result["fx_rates"] = fx
    return result


@api_router.post("/estimator/calculate-fast")
async def calculate_fast(inp: ProjectInputs):
    """Same as calculate but skips AI (for live slider preview)."""
    return compute_estimate(inp)


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
