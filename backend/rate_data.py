"""Static rate database derived from MDLZ cost evaluation and estimator framework.
All base rates are in USD per unit.  Regional multipliers adjust for location.
"""
from typing import Dict

# Base activity rates (USD) - Civil + Utilities BOQ items
CIVIL_ACTIVITIES = [
    # (activity, unit, base_rate_usd, category)
    ("Excavation", "m³", 12.50, "Earthwork"),
    ("PCC (M10)", "m³", 82.00, "Foundation"),
    ("RCC Foundation (Raft)", "m³", 165.00, "Foundation"),
    ("Structural Steel (PEB)", "MT", 1250.00, "Superstructure"),
    ("RCC Superstructure", "m³", 178.00, "Superstructure"),
    ("Roofing (Insulated Panel)", "m²", 36.00, "Roofing"),
    ("Flooring (Epoxy + PU)", "m²", 32.00, "Finishing"),
    ("Walls (Block + Plaster + Tile)", "m²", 48.00, "Finishing"),
    ("Plumbing & Sanitary", "LS", 285000.00, "MEP"),
    ("External Works & Roads", "m²", 42.00, "Infra"),
    ("Compound Wall / Fence", "m", 95.00, "Infra"),
    ("Landscaping", "m²", 18.00, "Infra"),
]

# Utilities systems - typed by discipline for city-specific pricing
# (name, unit, base_rate_usd, discipline: "mechanical" | "electrical" | "civil")
UTILITY_SYSTEMS = [
    ("Water Supply System",       "LS",  920000.00, "civil"),
    ("Steam & Boiler System",     "LS", 1620000.00, "mechanical"),
    ("Refrigeration / Cold Chain","LS", 2450000.00, "mechanical"),
    ("Compressed Air System",     "LS",  780000.00, "mechanical"),
    ("Electrical Infrastructure", "LS", 1980000.00, "electrical"),
    ("ETP / STP System",          "LS",  950000.00, "civil"),
    ("Fire Fighting System",      "LS",  450000.00, "mechanical"),
]

# Regional cost multipliers (relative to global base)
REGION_MULTIPLIERS = {
    "North America": 1.35,
    "Europe": 1.15,
    "Middle East": 0.95,
    "India / South Asia": 0.55,
    "ASEAN": 0.70,
    "Africa": 0.80,
    "Latin America": 0.85,
    "Oceania": 1.25,
    "Asia": 0.75,
    "South America": 0.85,
}

# Country tier factor (metro/non-metro/remote)
LOCATION_FACTOR = {
    "Metro": 1.00,
    "Non-Metro": 0.92,
    "Remote": 1.18,
}

# Complexity multipliers - toggleable
COMPLEXITY_FACTORS = {
    "seismic_zone_high": 1.06,
    "high_humidity": 1.04,
    "cold_region": 1.05,
    "brownfield": 1.08,
    "gmp_hygienic": 1.09,
    "explosion_risk": 1.07,
    "utility_redundancy": 1.11,
    "high_floor_load": 1.05,
    "remote_site": 1.12,
}

# Industry preset (share of total cost between building & utilities)
INDUSTRY_PRESETS = {
    "Chocolate Plant": {"utilities_pct": 0.42, "cold_chain_pct": 0.20, "hvac_pct": 0.14},
    "Biscuit Plant": {"utilities_pct": 0.35, "cold_chain_pct": 0.05, "hvac_pct": 0.10},
    "Wafer / Cookies": {"utilities_pct": 0.33, "cold_chain_pct": 0.06, "hvac_pct": 0.09},
    "Confectionery Mixed Plant": {"utilities_pct": 0.40, "cold_chain_pct": 0.15, "hvac_pct": 0.12},
    "Bakery + Chocolate Combo": {"utilities_pct": 0.44, "cold_chain_pct": 0.18, "hvac_pct": 0.13},
    "FMCG": {"utilities_pct": 0.30, "cold_chain_pct": 0.04, "hvac_pct": 0.08},
    "Warehouse / Logistics": {"utilities_pct": 0.18, "cold_chain_pct": 0.02, "hvac_pct": 0.05},
    "Process Building": {"utilities_pct": 0.38, "cold_chain_pct": 0.10, "hvac_pct": 0.10},
}

# Compliance / GMP finish adder (% of building cost)
COMPLIANCE_ADDER_PCT = 0.09

# Contingency default
CONTINGENCY_PCT = 0.08

# Currency symbols
CURRENCY_SYMBOLS = {
    "USD": "$", "EUR": "€", "GBP": "£", "INR": "₹", "JPY": "¥",
    "AUD": "A$", "CAD": "C$", "CHF": "CHF", "CNY": "¥", "SGD": "S$",
    "AED": "د.إ", "ZAR": "R", "BRL": "R$", "MXN": "Mex$",
}

# ---------- City-specific cost factors ----------
# Each city defines its own multipliers for: civil (materials + basic works),
# mechanical (HVAC, boiler, compressed air, refrigeration),
# electrical (substation, DG, distribution), and labour (skilled + unskilled).
# All factors are relative to the region baseline (1.00).
# Unknown cities fall back to a neutral profile.
CITY_FACTORS = {
    # -------------------- India Tier-1 Metros --------------------
    "mumbai":      {"civil": 1.18, "mechanical": 1.15, "electrical": 1.16, "labour": 1.35},
    "navi mumbai": {"civil": 1.14, "mechanical": 1.12, "electrical": 1.13, "labour": 1.28},
    "thane":       {"civil": 1.12, "mechanical": 1.10, "electrical": 1.12, "labour": 1.25},
    "delhi":       {"civil": 1.15, "mechanical": 1.12, "electrical": 1.14, "labour": 1.28},
    "new delhi":   {"civil": 1.15, "mechanical": 1.12, "electrical": 1.14, "labour": 1.28},
    "gurgaon":     {"civil": 1.16, "mechanical": 1.14, "electrical": 1.15, "labour": 1.30},
    "gurugram":    {"civil": 1.16, "mechanical": 1.14, "electrical": 1.15, "labour": 1.30},
    "noida":       {"civil": 1.14, "mechanical": 1.13, "electrical": 1.14, "labour": 1.26},
    "faridabad":   {"civil": 1.10, "mechanical": 1.09, "electrical": 1.10, "labour": 1.18},
    "bangalore":   {"civil": 1.12, "mechanical": 1.10, "electrical": 1.12, "labour": 1.25},
    "bengaluru":   {"civil": 1.12, "mechanical": 1.10, "electrical": 1.12, "labour": 1.25},
    "chennai":     {"civil": 1.08, "mechanical": 1.08, "electrical": 1.09, "labour": 1.15},
    "hyderabad":   {"civil": 1.05, "mechanical": 1.06, "electrical": 1.07, "labour": 1.10},
    "pune":        {"civil": 1.10, "mechanical": 1.09, "electrical": 1.10, "labour": 1.18},
    "kolkata":     {"civil": 0.95, "mechanical": 1.00, "electrical": 1.02, "labour": 0.92},
    "ahmedabad":   {"civil": 0.98, "mechanical": 1.02, "electrical": 1.03, "labour": 0.94},
    # -------------------- India Tier-2 --------------------
    "surat":       {"civil": 0.94, "mechanical": 0.98, "electrical": 0.99, "labour": 0.90},
    "vadodara":    {"civil": 0.93, "mechanical": 0.97, "electrical": 0.98, "labour": 0.88},
    "baroda":      {"civil": 0.93, "mechanical": 0.97, "electrical": 0.98, "labour": 0.88},
    "jaipur":      {"civil": 0.92, "mechanical": 0.96, "electrical": 0.97, "labour": 0.86},
    "lucknow":     {"civil": 0.90, "mechanical": 0.95, "electrical": 0.96, "labour": 0.84},
    "kanpur":      {"civil": 0.88, "mechanical": 0.94, "electrical": 0.95, "labour": 0.80},
    "coimbatore":  {"civil": 0.93, "mechanical": 0.97, "electrical": 0.98, "labour": 0.88},
    "kochi":       {"civil": 0.95, "mechanical": 0.99, "electrical": 1.00, "labour": 0.92},
    "cochin":      {"civil": 0.95, "mechanical": 0.99, "electrical": 1.00, "labour": 0.92},
    "indore":      {"civil": 0.89, "mechanical": 0.94, "electrical": 0.95, "labour": 0.82},
    "nagpur":      {"civil": 0.88, "mechanical": 0.94, "electrical": 0.95, "labour": 0.82},
    "bhopal":      {"civil": 0.87, "mechanical": 0.93, "electrical": 0.94, "labour": 0.80},
    "chandigarh":  {"civil": 0.96, "mechanical": 1.00, "electrical": 1.02, "labour": 0.95},
    "bhubaneswar": {"civil": 0.87, "mechanical": 0.93, "electrical": 0.94, "labour": 0.80},
    "visakhapatnam":{"civil": 0.90, "mechanical": 0.95, "electrical": 0.96, "labour": 0.85},
    "guwahati":    {"civil": 0.88, "mechanical": 0.96, "electrical": 0.97, "labour": 0.82},
    "raipur":      {"civil": 0.85, "mechanical": 0.92, "electrical": 0.93, "labour": 0.78},
    "ranchi":      {"civil": 0.85, "mechanical": 0.92, "electrical": 0.93, "labour": 0.78},
    "goa":         {"civil": 1.02, "mechanical": 1.05, "electrical": 1.05, "labour": 1.00},
    "panaji":      {"civil": 1.02, "mechanical": 1.05, "electrical": 1.05, "labour": 1.00},
    "mysore":      {"civil": 0.92, "mechanical": 0.97, "electrical": 0.98, "labour": 0.86},
    "trivandrum":  {"civil": 0.92, "mechanical": 0.96, "electrical": 0.97, "labour": 0.88},
    "madurai":     {"civil": 0.90, "mechanical": 0.95, "electrical": 0.96, "labour": 0.86},
    "nashik":      {"civil": 0.94, "mechanical": 0.98, "electrical": 0.99, "labour": 0.90},
    "aurangabad":  {"civil": 0.90, "mechanical": 0.95, "electrical": 0.96, "labour": 0.85},
    "dehradun":    {"civil": 0.90, "mechanical": 0.94, "electrical": 0.95, "labour": 0.85},
    # -------------------- Europe --------------------
    "hamburg":     {"civil": 1.05, "mechanical": 1.04, "electrical": 1.05, "labour": 1.18},
    "berlin":      {"civil": 1.03, "mechanical": 1.03, "electrical": 1.04, "labour": 1.15},
    "munich":      {"civil": 1.12, "mechanical": 1.06, "electrical": 1.08, "labour": 1.28},
    "frankfurt":   {"civil": 1.08, "mechanical": 1.05, "electrical": 1.06, "labour": 1.22},
    "cologne":     {"civil": 1.04, "mechanical": 1.03, "electrical": 1.05, "labour": 1.16},
    "paris":       {"civil": 1.15, "mechanical": 1.08, "electrical": 1.10, "labour": 1.28},
    "lyon":        {"civil": 1.05, "mechanical": 1.04, "electrical": 1.06, "labour": 1.15},
    "london":      {"civil": 1.35, "mechanical": 1.20, "electrical": 1.22, "labour": 1.45},
    "manchester":  {"civil": 1.12, "mechanical": 1.10, "electrical": 1.12, "labour": 1.22},
    "milan":       {"civil": 1.08, "mechanical": 1.05, "electrical": 1.07, "labour": 1.15},
    "rome":        {"civil": 1.06, "mechanical": 1.05, "electrical": 1.07, "labour": 1.14},
    "madrid":      {"civil": 0.98, "mechanical": 1.00, "electrical": 1.02, "labour": 0.95},
    "barcelona":   {"civil": 1.00, "mechanical": 1.02, "electrical": 1.03, "labour": 0.98},
    "amsterdam":   {"civil": 1.12, "mechanical": 1.08, "electrical": 1.10, "labour": 1.22},
    "warsaw":      {"civil": 0.82, "mechanical": 0.88, "electrical": 0.90, "labour": 0.62},
    "prague":      {"civil": 0.84, "mechanical": 0.90, "electrical": 0.92, "labour": 0.68},
    "budapest":    {"civil": 0.80, "mechanical": 0.86, "electrical": 0.88, "labour": 0.58},
    # -------------------- North America --------------------
    "new york":    {"civil": 1.45, "mechanical": 1.30, "electrical": 1.35, "labour": 1.60},
    "los angeles": {"civil": 1.35, "mechanical": 1.25, "electrical": 1.28, "labour": 1.50},
    "chicago":     {"civil": 1.30, "mechanical": 1.20, "electrical": 1.25, "labour": 1.45},
    "houston":     {"civil": 1.15, "mechanical": 1.10, "electrical": 1.12, "labour": 1.25},
    "dallas":      {"civil": 1.12, "mechanical": 1.08, "electrical": 1.10, "labour": 1.22},
    "atlanta":     {"civil": 1.10, "mechanical": 1.05, "electrical": 1.08, "labour": 1.18},
    "boston":      {"civil": 1.35, "mechanical": 1.20, "electrical": 1.25, "labour": 1.50},
    "toronto":     {"civil": 1.22, "mechanical": 1.15, "electrical": 1.18, "labour": 1.32},
    "montreal":    {"civil": 1.10, "mechanical": 1.08, "electrical": 1.10, "labour": 1.20},
    "vancouver":   {"civil": 1.25, "mechanical": 1.18, "electrical": 1.20, "labour": 1.38},
    "mexico city": {"civil": 0.75, "mechanical": 0.82, "electrical": 0.85, "labour": 0.42},
    # -------------------- Middle East / ASEAN --------------------
    "dubai":       {"civil": 1.05, "mechanical": 1.08, "electrical": 1.10, "labour": 0.85},
    "abu dhabi":   {"civil": 1.06, "mechanical": 1.09, "electrical": 1.10, "labour": 0.88},
    "riyadh":      {"civil": 1.02, "mechanical": 1.05, "electrical": 1.07, "labour": 0.80},
    "doha":        {"civil": 1.08, "mechanical": 1.10, "electrical": 1.11, "labour": 0.88},
    "singapore":   {"civil": 1.28, "mechanical": 1.20, "electrical": 1.22, "labour": 1.30},
    "kuala lumpur":{"civil": 0.85, "mechanical": 0.92, "electrical": 0.94, "labour": 0.58},
    "jakarta":     {"civil": 0.78, "mechanical": 0.86, "electrical": 0.88, "labour": 0.45},
    "bangkok":     {"civil": 0.85, "mechanical": 0.92, "electrical": 0.94, "labour": 0.55},
    "manila":      {"civil": 0.80, "mechanical": 0.88, "electrical": 0.90, "labour": 0.48},
    "hong kong":   {"civil": 1.35, "mechanical": 1.25, "electrical": 1.28, "labour": 1.45},
    "tokyo":       {"civil": 1.40, "mechanical": 1.30, "electrical": 1.32, "labour": 1.55},
    "shanghai":    {"civil": 0.95, "mechanical": 1.00, "electrical": 1.02, "labour": 0.85},
    "sydney":      {"civil": 1.25, "mechanical": 1.18, "electrical": 1.20, "labour": 1.35},
    "melbourne":   {"civil": 1.22, "mechanical": 1.15, "electrical": 1.18, "labour": 1.32},
    # -------------------- Africa / LatAm --------------------
    "cairo":       {"civil": 0.68, "mechanical": 0.78, "electrical": 0.80, "labour": 0.35},
    "johannesburg":{"civil": 0.85, "mechanical": 0.92, "electrical": 0.94, "labour": 0.62},
    "lagos":       {"civil": 0.80, "mechanical": 0.88, "electrical": 0.90, "labour": 0.50},
    "sao paulo":   {"civil": 0.92, "mechanical": 0.98, "electrical": 1.00, "labour": 0.72},
    "rio de janeiro":{"civil": 0.90, "mechanical": 0.96, "electrical": 0.98, "labour": 0.70},
    "buenos aires":{"civil": 0.72, "mechanical": 0.80, "electrical": 0.82, "labour": 0.55},
}

# Neutral fallback profile when the entered city is not in the table
NEUTRAL_CITY_PROFILE = {"civil": 1.00, "mechanical": 1.00, "electrical": 1.00, "labour": 1.00}


def city_factor_lookup(city_name: str) -> Dict[str, float]:
    """Case- and space-insensitive city lookup. Falls back to NEUTRAL profile."""
    if not city_name:
        return dict(NEUTRAL_CITY_PROFILE, matched=False, resolved=None)
    key = " ".join(city_name.strip().lower().split())
    if key in CITY_FACTORS:
        d = dict(CITY_FACTORS[key])
        d["matched"] = True
        d["resolved"] = key.title()
        return d
    # Try each token separately for compound city names like "Mumbai Metropolitan"
    for token in key.split():
        if token in CITY_FACTORS:
            d = dict(CITY_FACTORS[token])
            d["matched"] = True
            d["resolved"] = token.title()
            return d
    return dict(NEUTRAL_CITY_PROFILE, matched=False, resolved=None)
