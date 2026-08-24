"""Static rate database derived from MDLZ cost evaluation and estimator framework.
All base rates are in USD per unit.  Regional multipliers adjust for location.
"""
'''from typing import Dict

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
    return dict(NEUTRAL_CITY_PROFILE, matched=False, resolved=None)'''
    
from typing import Dict

# ============================================================================
# MDLZ / Bilfinger Tebodin cost benchmark (Czech Republic, rev 00, 01/2026)
# ----------------------------------------------------------------------------
# Source: "MDLZ_Cost_evaluation_250120_to_be_completed.xlsx"
#   TOTAL CONSTRUCTION COSTS ....... 650,131,904 CZK =  30,056,954 USD (100%)
#   A  Production building (frozen). 221,085,337 CZK =  10,221,236 USD ( 34%)
#   B  Final good storage ...........  28,951,646 CZK =   1,338,495 USD (  4%)
#   C  Social annex .................   5,158,530 CZK =     238,490 USD (  1%)
#   D  Maintenance ..................  32,341,249 CZK =   1,495,203 USD (  5%)
#   E  Waste yard ...................  22,328,394 CZK =   1,032,288 USD (  3%)
#   F  Lockers + corridor ...........  49,452,285 CZK =   2,286,282 USD (  8%)
#   G  Office building ..............  35,608,325 CZK =   1,646,247 USD (  5%)
#   H  Energocentre (chiller) .......  27,423,058 CZK =   1,267,825 USD (  4%)
#   I  Small / utility buildings ....  51,680,077 CZK =   2,389,278 USD (  8%)
#   J  Other (CCTV/BMS) .............  23,944,445 CZK =   1,107,002 USD (  4%)
#   K  External works ...............  78,823,700 CZK =   3,644,184 USD ( 12%)
#   P  Preliminaries ................  52,884,729 CZK =   2,444,971 USD (  8%)
#   TM Temporary measures ...........  20,450,130 CZK =     945,452 USD (  3%)
#   TECH Technology & utilities ..... 108,449,492 CZK =   5,013,846 USD
#   FURNITURE .......................   6,996,732 CZK =     323,474 USD
# Contract FX: CZK/USD = 21.630  (live CZK ~ 21.1 is fetched at runtime)
# ----------------------------------------------------------------------------
# Base rates below are the Excel unit prices converted to USD. They feed the
# existing server.py unchanged (same variable names -> same response schema,
# so the UI/frontend does not need any modification).
# ============================================================================

# Base activity rates (USD) - Civil + Utilities BOQ items
# Calibrated against the MDLZ benchmark (Europe / Czech Republic level).
CIVIL_ACTIVITIES = [
    # (activity, unit, base_rate_usd, category)
    ("Excavation", "m³", 28.00, "Earthwork"),                    # K: Earthworks 15,239,482 CZK = 704,553 USD
    ("PCC (M10)", "m³", 120.00, "Foundation"),                   # B: floor sublayers ~1,190 CZK/m² of slab
    ("RCC Foundation (Raft)", "m³", 185.00, "Foundation"),        # B: foundations 2,655 CZK/m² (incl. gravel piles 1,660)
    ("Structural Steel (PEB)", "MT", 1300.00, "Superstructure"),  # B: columns 2,611 + roof struct. 1,009 CZK/m² ~ 3,040 USD/MT
    ("RCC Superstructure", "m³", 315.00, "Superstructure"),       # EU RCC columns/beams benchmark
    ("Roofing (Insulated Panel)", "m²", 39.00, "Roofing"),       # B: roof 3,273 CZK/m² = 151 USD/m² (trapez. + TI + foil)
    ("Flooring (Epoxy + PU)", "m²", 29.00, "Finishing"),          # B: floor slab 1,999 + finishes 793 CZK/m²
    ("Walls (Block + Plaster + Tile)", "m²", 82.00, "Finishing"), # B/F: vertical structures + vertical surfaces
    ("Plumbing & Sanitary", "LS",  240200.00, "MEP"),              # A: water + sanitary 333,706 USD (9,829 m²) + plant-wide
    ("External Works & Roads", "m²", 48.00, "Infra"),            # K: roads 32,846,351 CZK = 1,518,555 USD / ~14,246 m² paving
    ("Compound Wall / Fence", "m", 145.00, "Infra"),              # K: fence 2,678 CZK/m = 124 USD/m + gates/barriers
    ("Landscaping", "m²", 4.74, "Infra"),                         # K: greenery 757,624 CZK = 35,027 USD / 7,390 m²
]

# Utilities systems - typed by discipline for city-specific pricing
# (name, unit, base_rate_usd, discipline: "mechanical" | "electrical" | "civil")
UTILITY_SYSTEMS = [
    ("Water Supply System",        "LS",   240200.00, "civil"),       # A: water+sewage 265,033 USD (9,829 m²) + other bldgs ~ 653K
    ("Steam & Boiler System",      "LS", 720012.00, "mechanical"),  # not in MDLZ CZK sheet (direct-gas ovens) - kept at benchmark
    ("Refrigeration / Cold Chain", "LS", 901000.00, "mechanical"),  # H: chiller install 27.42M CZK = 1,267,825 USD + A: cooling 409,804
    ("Compressed Air System",      "LS",  40500.00, "mechanical"),  # A: 2.7 compressed air 14.13M CZK = 653,164 USD incl. compressor set
    ("Electrical Infrastructure",  "LS", 1000005.00, "electrical"),  # A: bldg electrical 1,577,850 USD + TS5/TS6 + ext. HV/LV 396,187
    ("HVAC",           "LS", 400000.00, "civil"),    
    ("Utility Piping",           "LS", 877500.00, "civil"),# not in CZK sheet; Poland "sewage pretreatment 4.5M PLN" ~ 1.15M USD
    ("Fire Fighting System",       "LS", 500001.00, "mechanical"),  # A: sprinklers 191,728 + hydrants 7,277 + I: sprinkler station 304,360
]

# Regional cost multipliers (relative to global base)
REGION_MULTIPLIERS = {
    "AMEA": {
        "India": 0.41,
        "China": 0.58,
        "UAE": 0.85,
        "Saudi Arabia": 0.72,
        "South Africa": 0.45,
        "Egypt": 0.30,
        "Thailand": 0.42,
        "Vietnam": 0.38,
        "Indonesia": 0.40,
        "Australia": 1.52,
        "New Zealand": 1.35,
    },

    "MEU": {
        "Germany": 1.13,
        "France": 1.10,
        "UK": 1.05,
        "Netherlands": 1.15,
        "Switzerland": 1.65,
        "Poland": 0.55,
        "Czech Republic": 0.60,
        "Italy": 0.95,
        "Spain": 0.85,
        "Norway": 1.80,
        "Sweden": 1.25,
    },

    "North America": {
        "USA": 1.00,
        "Canada": 1.15,
        "Mexico": 0.52,
    },

    "Latin America": {
        "Brazil": 0.48,
        "Argentina": 0.35,
        "Colombia": 0.38,
        "Chile": 0.55,
        "Peru": 0.40,
    },
}

# Country tier factor (metro/non-metro/remote)
LOCATION_FACTOR = {
    "Metro": 1.00,
    "Non-Metro": 0.92,
    "Remote": 1.10,
}

# Complexity multipliers - toggleable
COMPLEXITY_FACTORS = {
    "seismic_zone_high": 1.12,
    "high_humidity": 1.06,
    "cold_region": 1.08,
    "brownfield": 1.15,
    "gmp_hygienic": 1.18,
    "explosion_risk": 1.10,
    "utility_redundancy": 1.15,
    "high_floor_load": 1.07,
    "remote_site": 1.12,
    "remote_location_civil" :1.10,
    "seismic_zone_moderate" :1.05,
    "height_over_12m":1.08,
    "brownfield_civil":1.12,
    "coastal_corrosion": 1.10 
}

# Industry preset (share of total cost between building & utilities)
INDUSTRY_PRESETS = {
    "Chocolate Plant": {"utilities_pct": 0.63, "cold_chain_pct": 0.18, "hvac_pct": 0.11},
    "Biscuit Plant": {"utilities_pct": 0.50, "cold_chain_pct": 0.05, "hvac_pct": 0.09},
    "Bakery + Chocolate Combo": {"utilities_pct": 0.60, "cold_chain_pct": 0.16, "hvac_pct": 0.11},
    "Warehouse": {"utilities_pct": 0.25, "cold_chain_pct": 0.02, "hvac_pct": 0.04},
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
    "CZK": "Kč",  # added for the MDLZ (Czech Republic) benchmark
}

# ---------- City-specific cost factors ----------
# Each city defines its own multipliers for: civil (materials + basic works),
# mechanical (HVAC, boiler, compressed air, refrigeration),
# electrical (substation, DG, distribution), and labour (skilled + unskilled).
# All factors are relative to the region baseline (1.00).
# Unknown cities fall back to a neutral profile.
# NOTE: "prague" below reproduces the MDLZ Excel benchmark when combined with
#       Region = Europe, Tier = Metro.
CITY_FACTORS = {
 # -------------------- India Tier-1 Metros --------------------
    "mumbai":      {"civil": 1.05, "mechanical": 0.97, "electrical": 0.98, "labour": 1.09},
    "navi mumbai": {"civil": 0.98, "mechanical": 0.93, "electrical": 0.95, "labour": 1.01},
    "thane":       {"civil": 0.95, "mechanical": 0.90, "electrical": 0.93, "labour": 0.97},
    "delhi":       {"civil": 1.01, "mechanical": 0.95, "electrical": 0.97, "labour": 1.05},
    "new delhi":   {"civil": 1.01, "mechanical": 0.95, "electrical": 0.97, "labour": 1.05},
    "gurgaon":     {"civil": 1.03, "mechanical": 0.97, "electrical": 0.98, "labour": 1.06},
    "gurugram":    {"civil": 1.03, "mechanical": 0.97, "electrical": 0.98, "labour": 1.06},
    "noida":       {"civil": 0.98, "mechanical": 0.93, "electrical": 0.95, "labour": 1.01},
    "bangalore":   {"civil": 0.97, "mechanical": 0.93, "electrical": 0.95, "labour": 1.01},
    "bengaluru":   {"civil": 0.97, "mechanical": 0.93, "electrical": 0.95, "labour": 1.01},
    "chennai":     {"civil": 0.90, "mechanical": 0.89, "electrical": 0.90, "labour": 0.93},
    "hyderabad":   {"civil": 0.89, "mechanical": 0.87, "electrical": 0.89, "labour": 0.90},
    "pune":        {"civil": 0.93, "mechanical": 0.90, "electrical": 0.92, "labour": 0.95},
    "kolkata":     {"civil": 0.77, "mechanical": 0.79, "electrical": 0.83, "labour": 0.72},
    "ahmedabad":   {"civil": 0.81, "mechanical": 0.82, "electrical": 0.83, "labour": 0.77},
# -------------------- India Tier-2 --------------------
   

    "surat":        {"civil": 0.77, "mechanical": 0.79, "electrical": 0.80, "labour": 0.71},
    "vadodara":     {"civil": 0.75, "mechanical": 0.77, "electrical": 0.78, "labour": 0.68},
    "jaipur":       {"civil": 0.74, "mechanical": 0.77, "electrical": 0.77, "labour": 0.66},
    "lucknow":      {"civil": 0.71, "mechanical": 0.74, "electrical": 0.75, "labour": 0.63},
    "coimbatore":   {"civil": 0.75, "mechanical": 0.77, "electrical": 0.78, "labour": 0.68},
    "kochi":        {"civil": 0.77, "mechanical": 0.80, "electrical": 0.81, "labour": 0.72},
    "indore":       {"civil": 0.71, "mechanical": 0.74, "electrical": 0.75, "labour": 0.63},
    "nagpur":       {"civil": 0.70, "mechanical": 0.74, "electrical": 0.75, "labour": 0.61},
    "bhubaneswar":  {"civil": 0.70, "mechanical": 0.73, "electrical": 0.74, "labour": 0.58},
    "cuttack":      {"civil": 0.67, "mechanical": 0.71, "electrical": 0.72, "labour": 0.55},
     "sricity":      {"civil": 0.82, "mechanical": 0.84, "electrical": 0.85, "labour": 0.80},
    
    

# -------------------- Europe --------------------

   "prague":       {"civil": 0.77, "mechanical": 0.77, "electrical": 0.77, "labour": 0.77},
   "warsaw":       {"civil": 0.75, "mechanical": 0.75, "electrical": 0.75, "labour": 0.75},
   "budapest":     {"civil": 0.74, "mechanical": 0.74, "electrical": 0.74, "labour": 0.71},
   "berlin":       {"civil": 1.01, "mechanical": 1.01, "electrical": 1.01, "labour": 1.01},
   "munich":       {"civil": 1.12, "mechanical": 1.07, "electrical": 1.08, "labour": 1.17},
   "hamburg":      {"civil": 1.05, "mechanical": 1.03, "electrical": 1.03, "labour": 1.07},
   "frankfurt":    {"civil": 1.08, "mechanical": 1.05, "electrical": 1.06, "labour": 1.12},
   "paris":        {"civil": 1.12, "mechanical": 1.06, "electrical": 1.08, "labour": 1.18},
   "lyon":         {"civil": 1.02, "mechanical": 1.01, "electrical": 1.02, "labour": 1.05},
   "london":       {"civil": 1.27, "mechanical": 1.15, "electrical": 1.17, "labour": 1.37},
   "manchester":   {"civil": 1.08, "mechanical": 1.03, "electrical": 1.06, "labour": 1.10},
   "amsterdam":    {"civil": 1.11, "mechanical": 1.07, "electrical": 1.09, "labour": 1.15},
   "milan":        {"civil": 0.98, "mechanical": 0.96, "electrical": 0.97, "labour": 1.01},
   "rome":         {"civil": 0.95, "mechanical": 0.95, "electrical": 0.96, "labour": 0.98},
   "madrid":       {"civil": 0.89, "mechanical": 0.89, "electrical": 0.89, "labour": 0.89},
   "barcelona":    {"civil": 0.90, "mechanical": 0.90, "electrical": 0.90, "labour": 0.91},

# -------------------- North America --------------------
   "new york":     {"civil": 1.43, "mechanical": 1.30, "electrical": 1.33, "labour": 1.59},
   "los angeles":  {"civil": 1.36, "mechanical": 1.25, "electrical": 1.27, "labour": 1.49},
   "chicago":      {"civil": 1.30, "mechanical": 1.22, "electrical": 1.25, "labour": 1.43},
   "houston":      {"civil": 1.15, "mechanical": 1.11, "electrical": 1.13, "labour": 1.22},
   "dallas":       {"civil": 1.11, "mechanical": 1.09, "electrical": 1.10, "labour": 1.19},
   "atlanta":      {"civil": 1.09, "mechanical": 1.08, "electrical": 1.09, "labour": 1.15},
   "toronto":      {"civil": 1.20, "mechanical": 1.18, "electrical": 1.19, "labour": 1.24},
   "vancouver":    {"civil": 1.26, "mechanical": 1.21, "electrical": 1.24, "labour": 1.32},
   "montreal":     {"civil": 1.09, "mechanical": 1.12, "electrical": 1.13, "labour": 1.09},
   "mexico city":  {"civil": 0.79, "mechanical": 0.79, "electrical": 0.79, "labour": 0.79},

# -------------------- Middle East / ASEAN --------------------

   "dubai":        {"civil": 1.13, "mechanical": 1.16, "electrical": 1.17, "labour": 0.91},
   "abu dhabi":    {"civil": 1.16, "mechanical": 1.17, "electrical": 1.18, "labour": 0.93},
   "riyadh":       {"civil": 1.04, "mechanical": 1.06, "electrical": 1.07, "labour": 0.81},
   "singapore":    {"civil": 1.30, "mechanical": 1.25, "electrical": 1.27, "labour": 1.36},
   "kuala lumpur": {"civil": 0.85, "mechanical": 0.84, "electrical": 0.85, "labour": 0.77},
   "jakarta":      {"civil": 0.80, "mechanical": 0.80, "electrical": 0.80, "labour": 0.72},
   "bangkok":      {"civil": 0.83, "mechanical": 0.83, "electrical": 0.84, "labour": 0.75},
   "hong kong":    {"civil": 1.36, "mechanical": 1.30, "electrical": 1.31, "labour": 1.53},
   "tokyo":        {"civil": 1.37, "mechanical": 1.34, "electrical": 1.37, "labour": 1.56},
"shanghai":     {"civil": 0.98, "mechanical": 0.96, "electrical": 0.97, "labour": 0.93},

# -------------------- Oceania --------------------

   "sydney":       {"civil": 1.63, "mechanical": 1.63, "electrical": 1.63, "labour": 1.67},
   "melbourne":    {"civil": 1.60, "mechanical": 1.60, "electrical": 1.60, "labour": 1.63},

# -------------------- Africa / Latin America --------------------

   "cairo":        {"civil": 0.72, "mechanical": 0.72, "electrical": 0.72, "labour": 0.62},
   "johannesburg": {"civil": 0.88, "mechanical": 0.86, "electrical": 0.87, "labour": 0.84},
   "lagos":        {"civil": 0.76, "mechanical": 0.74, "electrical": 0.75, "labour": 0.69},
   "sao paulo":    {"civil": 1.14, "mechanical": 1.11, "electrical": 1.12, "labour": 1.16},
   "buenos aires": {"civil": 0.91, "mechanical": 0.91, "electrical": 0.91, "labour": 0.91},
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
