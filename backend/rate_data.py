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
    "buenos aires":{"civil": 0.72, "mechanical": 0.80, "electrical": 0.82, "labour":# K: E 0.55},
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
    
'''from typing import Dict

CIVIL_ACTIVITIES = [
    # (activity, unit, base_rate_usd, category)
    ("Excavation", "m³", 28.00, "Earthwork"),                    
    ("PCC (M10)", "m³", 120.00, "Foundation"),                  
    ("RCC Foundation (Raft)", "m³", 185.00, "Foundation"),        
    ("Structural Steel (PEB)", "MT", 1300.00, "Superstructure"),  
    ("RCC Superstructure", "m³", 315.00, "Superstructure"),      
    ("Roofing (Insulated Panel)", "m²", 39.00, "Roofing"),       
    ("Flooring (Epoxy + PU)", "m²", 29.00, "Finishing"),          
    ("Walls (Block + Plaster + Tile)", "m²", 82.00, "Finishing"), 
    ("Plumbing & Sanitary", "LS",  240200.00, "MEP"),              
    ("External Works & Roads", "m²", 48.00, "Infra"),            
    ("Compound Wall / Fence", "m", 145.00, "Infra"),              
    ("Landscaping", "m²", 4.74, "Infra"),                         
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
    return dict(NEUTRAL_CITY_PROFILE, matched=False, resolved=None)'''


# rate_data.py — USA = 1.00x base, image-verified benchmarks
# India $1,207 | Plonsk $2,641 | Opava $3,002 per m² ← VERIFIED
# ═══════════════════════════════════════════════════════════════════════════════

'''from typing import Dict, Any

# ───────────────────────────────────────────────────────────────
# USA BASE RATES (the 1.00x anchor)
# ───────────────────────────────────────────────────────────────
USA_BASE_CSA  = 650    # $/m² CSA at 1500 kg/m² floor load
USA_BASE_UTIL = 920    # $/m² utilities (full-length piping, all systems)

# ───────────────────────────────────────────────────────────────
# COUNTRY_COST_FACTORS (USA = 1.00)
# csa_factor  → × USA_BASE_CSA  = country CSA $/m² at @1500
# util_factor → × USA_BASE_UTIL = country utility $/m²
# others_pct  → % of (CSA+Util) for WH+ASRS, EPCM, Statutory, Staff
# ───────────────────────────────────────────────────────────────
COUNTRY_COST_FACTORS = {
    # ---- AMEA ----
    "India":            {"csa_factor": 0.612, "util_factor": 0.363, "others_pct": 0.649},
    "China":            {"csa_factor": 0.677, "util_factor": 0.457, "others_pct": 0.55},
    "UAE":              {"csa_factor": 0.815, "util_factor": 0.630, "others_pct": 0.65},
    "Saudi Arabia":     {"csa_factor": 0.769, "util_factor": 0.587, "others_pct": 0.60},
    "South Africa":     {"csa_factor": 0.585, "util_factor": 0.413, "others_pct": 0.55},
    "Egypt":            {"csa_factor": 0.492, "util_factor": 0.337, "others_pct": 0.50},
    "Thailand":         {"csa_factor": 0.554, "util_factor": 0.391, "others_pct": 0.53},
    "Vietnam":          {"csa_factor": 0.538, "util_factor": 0.370, "others_pct": 0.52},
    "Indonesia":        {"csa_factor": 0.531, "util_factor": 0.380, "others_pct": 0.52},
    "Australia":        {"csa_factor": 1.354, "util_factor": 1.000, "others_pct": 0.75},
    "New Zealand":      {"csa_factor": 1.292, "util_factor": 0.957, "others_pct": 0.73},
    "Japan":            {"csa_factor": 1.400, "util_factor": 1.100, "others_pct": 0.76},
    "South Korea":      {"csa_factor": 1.100, "util_factor": 0.870, "others_pct": 0.68},
    "Singapore":        {"csa_factor": 1.200, "util_factor": 0.960, "others_pct": 0.72},
    "Malaysia":         {"csa_factor": 0.620, "util_factor": 0.420, "others_pct": 0.53},
    "Philippines":      {"csa_factor": 0.500, "util_factor": 0.360, "others_pct": 0.50},
    "Bangladesh":       {"csa_factor": 0.440, "util_factor": 0.310, "others_pct": 0.48},
    "Pakistan":         {"csa_factor": 0.460, "util_factor": 0.320, "others_pct": 0.48},
    "Sri Lanka":        {"csa_factor": 0.480, "util_factor": 0.330, "others_pct": 0.49},
    # ---- MEU ----
    "Germany":          {"csa_factor": 1.308, "util_factor": 1.043, "others_pct": 0.75},
    "France":           {"csa_factor": 1.200, "util_factor": 1.000, "others_pct": 0.72},
    "UK":               {"csa_factor": 1.262, "util_factor": 0.978, "others_pct": 0.73},
    "Netherlands":      {"csa_factor": 1.292, "util_factor": 1.022, "others_pct": 0.74},
    "Belgium":          {"csa_factor": 1.260, "util_factor": 1.010, "others_pct": 0.73},
    "Switzerland":      {"csa_factor": 1.508, "util_factor": 1.196, "others_pct": 0.80},
    "Austria":          {"csa_factor": 1.280, "util_factor": 1.030, "others_pct": 0.74},
    "Poland":           {"csa_factor": 1.183, "util_factor": 0.879, "others_pct": 0.674},
    "Czech Republic":   {"csa_factor": 1.329, "util_factor": 0.879, "others_pct": 0.794},
    "Slovakia":         {"csa_factor": 1.150, "util_factor": 0.850, "others_pct": 0.66},
    "Hungary":          {"csa_factor": 1.100, "util_factor": 0.830, "others_pct": 0.65},
    "Romania":          {"csa_factor": 0.920, "util_factor": 0.700, "others_pct": 0.58},
    "Bulgaria":         {"csa_factor": 0.850, "util_factor": 0.650, "others_pct": 0.55},
    "Italy":            {"csa_factor": 0.954, "util_factor": 0.848, "others_pct": 0.68},
    "Spain":            {"csa_factor": 0.892, "util_factor": 0.783, "others_pct": 0.65},
    "Portugal":         {"csa_factor": 0.840, "util_factor": 0.740, "others_pct": 0.62},
    "Greece":           {"csa_factor": 0.880, "util_factor": 0.760, "others_pct": 0.63},
    "Turkey":           {"csa_factor": 0.720, "util_factor": 0.550, "others_pct": 0.55},
    "Norway":           {"csa_factor": 1.462, "util_factor": 1.174, "others_pct": 0.78},
    "Sweden":           {"csa_factor": 1.277, "util_factor": 1.043, "others_pct": 0.74},
    "Denmark":          {"csa_factor": 1.350, "util_factor": 1.080, "others_pct": 0.76},
    "Finland":          {"csa_factor": 1.300, "util_factor": 1.050, "others_pct": 0.75},
    "Ireland":          {"csa_factor": 1.240, "util_factor": 0.990, "others_pct": 0.72},
    # ---- North America ----
    "USA":              {"csa_factor": 1.000, "util_factor": 1.000, "others_pct": 0.72},
    "Canada":           {"csa_factor": 1.077, "util_factor": 1.043, "others_pct": 0.73},
    "Mexico":           {"csa_factor": 0.646, "util_factor": 0.457, "others_pct": 0.55},
    # ---- Latin America ----
    "Brazil":           {"csa_factor": 0.631, "util_factor": 0.435, "others_pct": 0.55},
    "Argentina":        {"csa_factor": 0.569, "util_factor": 0.391, "others_pct": 0.52},
    "Colombia":         {"csa_factor": 0.585, "util_factor": 0.402, "others_pct": 0.52},
    "Chile":            {"csa_factor": 0.662, "util_factor": 0.489, "others_pct": 0.55},
    "Peru":             {"csa_factor": 0.554, "util_factor": 0.380, "others_pct": 0.50},
    "Ecuador":          {"csa_factor": 0.520, "util_factor": 0.360, "others_pct": 0.50},
    "Uruguay":          {"csa_factor": 0.600, "util_factor": 0.420, "others_pct": 0.53},
    # ---- Africa ----
    "Nigeria":          {"csa_factor": 0.550, "util_factor": 0.400, "others_pct": 0.52},
    "Kenya":            {"csa_factor": 0.520, "util_factor": 0.380, "others_pct": 0.50},
    "Ghana":            {"csa_factor": 0.510, "util_factor": 0.370, "others_pct": 0.50},
    "Morocco":          {"csa_factor": 0.560, "util_factor": 0.400, "others_pct": 0.52},
    "Tunisia":          {"csa_factor": 0.540, "util_factor": 0.390, "others_pct": 0.51},
}


def get_country_cost_factors(country: str) -> Dict[str, float]:
    """Return csa_factor, util_factor, others_pct. Defaults to USA."""
    return COUNTRY_COST_FACTORS.get(country, COUNTRY_COST_FACTORS["USA"])



# Utility systems used by the estimator.
# (name, unit, base_rate_usd, discipline)
UTILITY_SYSTEMS = [
    ("Water Supply System",        "LS",  240200.00, "civil"),
    ("Steam & Boiler System",      "LS",  720012.00, "mechanical"),
    ("Refrigeration / Cold Chain", "LS",  901000.00, "mechanical"),
    ("Compressed Air System",     "LS",   40500.00, "mechanical"),
    ("Electrical Infrastructure", "LS", 1000005.00, "electrical"),
    ("HVAC",                       "LS",  400000.00, "civil"),
    ("Utility Piping",             "LS",  877500.00, "civil"),
    ("Fire Fighting System",       "LS",  500001.00, "mechanical"),
]


# Region -> country compatibility map.
# Numeric values reuse the existing country's csa_factor.
REGION_MULTIPLIERS = {
    "AMEA": {
        "India": 0.612, "China": 0.677, "UAE": 0.815, "Saudi Arabia": 0.769,
        "South Africa": 0.585, "Egypt": 0.492, "Thailand": 0.554, "Vietnam": 0.538,
        "Indonesia": 0.531, "Australia": 1.354, "New Zealand": 1.292, "Japan": 1.400,
        "South Korea": 1.100, "Singapore": 1.200, "Malaysia": 0.620,
        "Philippines": 0.500, "Bangladesh": 0.440, "Pakistan": 0.460, "Sri Lanka": 0.480,
    },
    "MEU": {
        "Germany": 1.308, "France": 1.200, "UK": 1.262, "Netherlands": 1.292,
        "Belgium": 1.260, "Switzerland": 1.508, "Austria": 1.280, "Poland": 1.183,
        "Czech Republic": 1.329, "Slovakia": 1.150, "Hungary": 1.100, "Romania": 0.920,
        "Bulgaria": 0.850, "Italy": 0.954, "Spain": 0.892, "Portugal": 0.840,
        "Greece": 0.880, "Turkey": 0.720, "Norway": 1.462, "Sweden": 1.277,
        "Denmark": 1.350, "Finland": 1.300, "Ireland": 1.240,
    },
    "North America": {"USA": 1.000, "Canada": 1.077, "Mexico": 0.646},
    "Latin America": {
        "Brazil": 0.631, "Argentina": 0.569, "Colombia": 0.585, "Chile": 0.662,
        "Peru": 0.554, "Ecuador": 0.520, "Uruguay": 0.600,
    },
    "Africa": {
        "Nigeria": 0.550, "Kenya": 0.520, "Ghana": 0.510, "Morocco": 0.560,
        "Tunisia": 0.540,
    },
}



# ───────────────────────────────────────────────────────────────
# UTILITY SYSTEM WEIGHTS (fraction of total utility cost)
# Sum = 1.00 — applied to (USA_BASE_UTIL × util_factor × built_up)
# ───────────────────────────────────────────────────────────────
UTILITY_SYSTEM_WEIGHTS = {
    "HVAC":                       (0.272, "mechanical",  "HVAC incl ductwork, AHUs, controls"),
    "Electrical Infrastructure":  (0.228, "electrical",  "HT/LT panels, transformers, cable trays"),
    "Utility Piping":             (0.113, "mechanical",  "HW 55/85C, chilled water, glycol, process"),
    "Steam & Boiler System":      (0.065, "mechanical",  "Steam header 10 bar, condensate, boiler"),
    "Refrigeration / Cold Chain": (0.098, "mechanical",  "Chillers, cooling towers, glycol loop"),
    "Fire Fighting System":       (0.092, "mechanical",  "Wet riser, sprinklers, hydrants, pump"),
    "Compressed Air System":      (0.033, "mechanical",  "Compressors, dryers, ring main 7 bar"),
    "Water Supply System":        (0.030, "civil",       "WTP, storage, distribution, softener"),
    "IT/OT System":               (0.035, "electrical",  "SCADA, MES, BMS, network backbone"),
    "Wastewater Treatment":       (0.034, "civil",       "WWTP, ETP, sludge handling"),
}

# ───────────────────────────────────────────────────────────────
# CIVIL ACTIVITIES — BOQ line items (USD, USA reference rates)
# ───────────────────────────────────────────────────────────────
CIVIL_ACTIVITIES = [
    ("Excavation",                     "m3",  28.00,   "Earthwork"),
    ("PCC (M10)",                      "m3",  120.00,  "Foundation"),
    ("RCC Foundation (Raft)",          "m3",  185.00,  "Foundation"),
    ("Structural Steel (PEB)",         "MT",  1300.00, "Superstructure"),
    ("RCC Superstructure",             "m3",  315.00,  "Superstructure"),
    ("Roofing (Insulated Panel)",      "m2",  39.00,   "Roofing"),
    ("Flooring (Epoxy + PU)",          "m2",  29.00,   "Finishing"),
    ("Walls (Block + Plaster + Tile)", "m2",  82.00,   "Finishing"),
    ("Plumbing & Sanitary",            "LS",  240200,  "MEP"),
    ("External Works & Roads",         "m2",  48.00,   "Infra"),
    ("Compound Wall / Fence",          "m",   145.00,  "Infra"),
    ("Landscaping",                    "m2",  4.74,    "Infra"),
]

# ───────────────────────────────────────────────────────────────
# LOCATION FACTOR
# ───────────────────────────────────────────────────────────────
LOCATION_FACTOR = {"Metro": 1.00, "Non-Metro": 0.92, "Remote": 1.10}

# ───────────────────────────────────────────────────────────────
# COMPLEXITY FACTORS
# ───────────────────────────────────────────────────────────────
COMPLEXITY_FACTORS = {
    "seismic_zone_high":      1.12,
    "high_humidity":          1.06,
    "cold_region":            1.08,
    "brownfield":             1.15,
    "gmp_hygienic":           1.18,     # benchmark default ON
    "explosion_risk":         1.10,
    "utility_redundancy":     1.15,     # benchmark default ON
    "remote_site":            1.12,
    "remote_location_civil":  1.10,
    "seismic_zone_moderate":  1.05,
    "height_over_12m":        1.08,
    "brownfield_civil":       1.12,
    "coastal_corrosion":      1.10,
}

# Benchmark = GMP(1.18) x Redundancy(1.15) = 1.357
BENCHMARK_COMPLEXITY_M = 1.357

# ───────────────────────────────────────────────────────────────
# BENCHMARK STRUCTURAL — the image reference scenario
# Raft+Hard+MedGWT+Zone2+Zone0+Steel+PEB+8m+24ms+1.2FAR+10.5m
# ───────────────────────────────────────────────────────────────
BENCHMARK_STRUCTURAL_M = 0.9440

# ───────────────────────────────────────────────────────────────
# PRODUCT CATEGORY → auto floor load (kN)
# ───────────────────────────────────────────────────────────────
PRODUCT_CATEGORY_LOAD = {
    "Chocolate Plant":          1500,
    "Bakery + Chocolate Combo": 1500,
    "Warehouse":                 750,
    "_default":                 1000,
}

# ───────────────────────────────────────────────────────────────
# FLOOR LOAD MULTIPLIER — relative to @1500 (the csa_factor ref)
# csa_factor calibrated AT 1500. Lower loads get a discount.
# Image: India @1000=$318, @1500=$398 → 318/398=0.799
# ───────────────────────────────────────────────────────────────
FLOOR_LOAD_REL_1500 = {
    750: {
        "India": 0.666, "China": 0.670, "UAE": 0.680, "Saudi Arabia": 0.675,
        "South Africa": 0.667, "Egypt": 0.665, "Thailand": 0.667, "Vietnam": 0.665,
        "Indonesia": 0.665, "Australia": 0.690, "New Zealand": 0.688,
        "Germany": 0.690, "France": 0.688, "UK": 0.688, "Netherlands": 0.690,
        "Switzerland": 0.695, "Poland": 0.680, "Czech Republic": 0.686,
        "Italy": 0.685, "Spain": 0.683, "Norway": 0.693, "Sweden": 0.690,
        "USA": 0.690, "Canada": 0.690, "Mexico": 0.670,
        "Brazil": 0.670, "Argentina": 0.665, "Colombia": 0.665,
        "Chile": 0.672, "Peru": 0.665,
        "_default": 0.680,
    },
    1000: {
        "India": 0.799, "China": 0.805, "UAE": 0.815, "Saudi Arabia": 0.810,
        "South Africa": 0.800, "Egypt": 0.798, "Thailand": 0.800, "Vietnam": 0.798,
        "Indonesia": 0.798, "Australia": 0.828, "New Zealand": 0.825,
        "Germany": 0.828, "France": 0.825, "UK": 0.825, "Netherlands": 0.828,
        "Switzerland": 0.832, "Poland": 0.773, "Czech Republic": 0.771,
        "Italy": 0.818, "Spain": 0.815, "Norway": 0.830, "Sweden": 0.828,
        "USA": 0.828, "Canada": 0.828, "Mexico": 0.805,
        "Brazil": 0.805, "Argentina": 0.798, "Colombia": 0.798,
        "Chile": 0.808, "Peru": 0.798,
        "_default": 0.810,
    },
    1500: {"_default": 1.000},
}


def get_floor_load_multiplier(product_category: str, country: str) -> Dict[str, Any]:
    """Auto-assign floor load, return multiplier relative to @1500."""
    load_kn = PRODUCT_CATEGORY_LOAD.get(product_category, PRODUCT_CATEGORY_LOAD["_default"])
    valid = sorted(FLOOR_LOAD_REL_1500.keys())
    snapped = min(valid, key=lambda x: abs(x - load_kn))
    table = FLOOR_LOAD_REL_1500[snapped]
    mult = table.get(country, table.get("_default", 1.0))
    return {"load_kn": load_kn, "snapped": snapped, "multiplier": round(mult, 4),
            "country": country, "product_category": product_category}


# ───────────────────────────────────────────────────────────────
# BENCHMARK CITY — per country (city_adj = 1.00 at benchmark)
# ───────────────────────────────────────────────────────────────
BENCHMARK_CITY = {
    "India":          "sricity",
    "Poland":         "plonsk",
    "Czech Republic": "opava",
    "USA":            "houston",
    "Germany":        "hamburg",
    "France":         "lyon",
    "UK":             "manchester",
    "China":          "shanghai",
    "Mexico":         "mexico city",
    "Brazil":         "sao paulo",
    "_default":       None,
}

# ───────────────────────────────────────────────────────────────
# EMPLOYEE FACILITY RATES (by country)
# ───────────────────────────────────────────────────────────────
EMPLOYEE_FACILITY_RATES = {
    "India":          {"civil_finish": 45,  "mep": 35,  "locker": 85,  "shoe_rack": 15, "bench": 40},
    "China":          {"civil_finish": 55,  "mep": 42,  "locker": 95,  "shoe_rack": 18, "bench": 48},
    "Thailand":       {"civil_finish": 48,  "mep": 38,  "locker": 88,  "shoe_rack": 16, "bench": 42},
    "Vietnam":        {"civil_finish": 42,  "mep": 33,  "locker": 80,  "shoe_rack": 14, "bench": 38},
    "Indonesia":      {"civil_finish": 44,  "mep": 34,  "locker": 82,  "shoe_rack": 14, "bench": 39},
    "Egypt":          {"civil_finish": 40,  "mep": 30,  "locker": 75,  "shoe_rack": 13, "bench": 35},
    "South Africa":   {"civil_finish": 52,  "mep": 40,  "locker": 95,  "shoe_rack": 17, "bench": 45},
    "UAE":            {"civil_finish": 85,  "mep": 70,  "locker": 165, "shoe_rack": 32, "bench": 80},
    "Saudi Arabia":   {"civil_finish": 78,  "mep": 62,  "locker": 150, "shoe_rack": 28, "bench": 72},
    "Australia":      {"civil_finish": 155, "mep": 130, "locker": 300, "shoe_rack": 52, "bench": 140},
    "New Zealand":    {"civil_finish": 140, "mep": 118, "locker": 275, "shoe_rack": 48, "bench": 128},
    "Poland":         {"civil_finish": 95,  "mep": 75,  "locker": 180, "shoe_rack": 30, "bench": 85},
    "Czech Republic": {"civil_finish": 105, "mep": 82,  "locker": 195, "shoe_rack": 35, "bench": 92},
    "Germany":        {"civil_finish": 145, "mep": 120, "locker": 280, "shoe_rack": 50, "bench": 130},
    "France":         {"civil_finish": 138, "mep": 115, "locker": 268, "shoe_rack": 48, "bench": 125},
    "UK":             {"civil_finish": 140, "mep": 115, "locker": 265, "shoe_rack": 48, "bench": 125},
    "Netherlands":    {"civil_finish": 148, "mep": 122, "locker": 285, "shoe_rack": 51, "bench": 132},
    "Switzerland":    {"civil_finish": 175, "mep": 145, "locker": 340, "shoe_rack": 60, "bench": 158},
    "Italy":          {"civil_finish": 118, "mep": 95,  "locker": 225, "shoe_rack": 40, "bench": 108},
    "Spain":          {"civil_finish": 108, "mep": 86,  "locker": 205, "shoe_rack": 37, "bench": 98},
    "Norway":         {"civil_finish": 180, "mep": 150, "locker": 350, "shoe_rack": 62, "bench": 165},
    "Sweden":         {"civil_finish": 155, "mep": 128, "locker": 298, "shoe_rack": 53, "bench": 138},
    "USA":            {"civil_finish": 165, "mep": 140, "locker": 320, "shoe_rack": 55, "bench": 150},
    "Canada":         {"civil_finish": 155, "mep": 130, "locker": 300, "shoe_rack": 52, "bench": 140},
    "Mexico":         {"civil_finish": 58,  "mep": 45,  "locker": 105, "shoe_rack": 20, "bench": 52},
    "Brazil":         {"civil_finish": 60,  "mep": 48,  "locker": 110, "shoe_rack": 21, "bench": 55},
    "Argentina":      {"civil_finish": 48,  "mep": 38,  "locker": 90,  "shoe_rack": 16, "bench": 42},
    "Colombia":       {"civil_finish": 50,  "mep": 40,  "locker": 92,  "shoe_rack": 17, "bench": 44},
    "Chile":          {"civil_finish": 68,  "mep": 55,  "locker": 128, "shoe_rack": 24, "bench": 62},
    "Peru":           {"civil_finish": 48,  "mep": 38,  "locker": 88,  "shoe_rack": 16, "bench": 42},
    "_default":       {"civil_finish": 85,  "mep": 68,  "locker": 160, "shoe_rack": 30, "bench": 75},
}


def get_employee_facility_rates(country: str) -> Dict[str, float]:
    return EMPLOYEE_FACILITY_RATES.get(country, EMPLOYEE_FACILITY_RATES["_default"])


# ───────────────────────────────────────────────────────────────
# INDUSTRY PRESETS
# ───────────────────────────────────────────────────────────────
INDUSTRY_PRESETS = {
    "Chocolate Plant":          {"utilities_pct": 0.63, "cold_chain_pct": 0.18, "hvac_pct": 0.11},
    "Bakery + Chocolate Combo": {"utilities_pct": 0.60, "cold_chain_pct": 0.16, "hvac_pct": 0.11},
    "Warehouse":                {"utilities_pct": 0.25, "cold_chain_pct": 0.02, "hvac_pct": 0.04},
}

COMPLIANCE_ADDER_PCT = 0.09
CONTINGENCY_PCT      = 0.08

CURRENCY_SYMBOLS = {
    "USD": "$", "EUR": "€", "GBP": "£", "INR": "₹", "JPY": "¥",
    "AUD": "A$", "CAD": "C$", "CHF": "CHF", "CNY": "¥", "SGD": "S$",
    "AED": "AED", "ZAR": "R", "BRL": "R$", "MXN": "Mex$", "CZK": "Kc",
    "PLN": "zl", "HUF": "Ft", "SEK": "kr", "NOK": "kr", "DKK": "kr",
}

# ───────────────────────────────────────────────────────────────
# CITY FACTORS — RAW discipline adjustments
# Normalized to benchmark city in compute_estimate()
# ───────────────────────────────────────────────────────────────
CITY_FACTORS = {
    # India
    "mumbai":      {"civil": 1.05, "mechanical": 0.97, "electrical": 0.98, "labour": 1.09},
    "navi mumbai": {"civil": 0.98, "mechanical": 0.93, "electrical": 0.95, "labour": 1.01},
    "delhi":       {"civil": 1.01, "mechanical": 0.95, "electrical": 0.97, "labour": 1.05},
    "gurgaon":     {"civil": 1.03, "mechanical": 0.97, "electrical": 0.98, "labour": 1.06},
    "noida":       {"civil": 0.98, "mechanical": 0.93, "electrical": 0.95, "labour": 1.01},
    "bangalore":   {"civil": 0.97, "mechanical": 0.93, "electrical": 0.95, "labour": 1.01},
    "chennai":     {"civil": 0.90, "mechanical": 0.89, "electrical": 0.90, "labour": 0.93},
    "hyderabad":   {"civil": 0.89, "mechanical": 0.87, "electrical": 0.89, "labour": 0.90},
    "pune":        {"civil": 0.93, "mechanical": 0.90, "electrical": 0.92, "labour": 0.95},
    "kolkata":     {"civil": 0.77, "mechanical": 0.79, "electrical": 0.83, "labour": 0.72},
    "ahmedabad":   {"civil": 0.81, "mechanical": 0.82, "electrical": 0.83, "labour": 0.77},
    "sricity":     {"civil": 0.82, "mechanical": 0.84, "electrical": 0.85, "labour": 0.80},
    "bhubaneswar": {"civil": 0.70, "mechanical": 0.73, "electrical": 0.74, "labour": 0.58},
    "indore":      {"civil": 0.71, "mechanical": 0.74, "electrical": 0.75, "labour": 0.63},
    "coimbatore":  {"civil": 0.75, "mechanical": 0.77, "electrical": 0.78, "labour": 0.68},
    "kochi":       {"civil": 0.77, "mechanical": 0.80, "electrical": 0.81, "labour": 0.72},
    "jaipur":      {"civil": 0.74, "mechanical": 0.77, "electrical": 0.77, "labour": 0.66},
    "lucknow":     {"civil": 0.71, "mechanical": 0.74, "electrical": 0.75, "labour": 0.63},
    # Europe
    "opava":       {"civil": 0.74, "mechanical": 0.74, "electrical": 0.74, "labour": 0.74},
    "prague":      {"civil": 0.77, "mechanical": 0.77, "electrical": 0.77, "labour": 0.77},
    "brno":        {"civil": 0.75, "mechanical": 0.75, "electrical": 0.75, "labour": 0.75},
    "plonsk":      {"civil": 0.72, "mechanical": 0.72, "electrical": 0.72, "labour": 0.72},
    "warsaw":      {"civil": 0.75, "mechanical": 0.75, "electrical": 0.75, "labour": 0.75},
    "krakow":      {"civil": 0.73, "mechanical": 0.73, "electrical": 0.73, "labour": 0.73},
    "wroclaw":     {"civil": 0.72, "mechanical": 0.72, "electrical": 0.72, "labour": 0.72},
    "gdansk":      {"civil": 0.71, "mechanical": 0.71, "electrical": 0.71, "labour": 0.71},
    "berlin":      {"civil": 1.01, "mechanical": 1.01, "electrical": 1.01, "labour": 1.01},
    "munich":      {"civil": 1.12, "mechanical": 1.07, "electrical": 1.08, "labour": 1.17},
    "hamburg":     {"civil": 1.05, "mechanical": 1.03, "electrical": 1.03, "labour": 1.07},
    "frankfurt":   {"civil": 1.08, "mechanical": 1.05, "electrical": 1.06, "labour": 1.12},
    "paris":       {"civil": 1.12, "mechanical": 1.06, "electrical": 1.08, "labour": 1.18},
    "lyon":        {"civil": 1.02, "mechanical": 1.01, "electrical": 1.02, "labour": 1.05},
    "london":      {"civil": 1.27, "mechanical": 1.15, "electrical": 1.17, "labour": 1.37},
    "manchester":  {"civil": 1.08, "mechanical": 1.03, "electrical": 1.06, "labour": 1.10},
    "amsterdam":   {"civil": 1.11, "mechanical": 1.07, "electrical": 1.09, "labour": 1.15},
    "milan":       {"civil": 0.98, "mechanical": 0.96, "electrical": 0.97, "labour": 1.01},
    "rome":        {"civil": 0.95, "mechanical": 0.95, "electrical": 0.96, "labour": 0.98},
    "madrid":      {"civil": 0.89, "mechanical": 0.89, "electrical": 0.89, "labour": 0.89},
    "barcelona":   {"civil": 0.90, "mechanical": 0.90, "electrical": 0.90, "labour": 0.91},
    # North America
    "new york":    {"civil": 1.43, "mechanical": 1.30, "electrical": 1.33, "labour": 1.59},
    "los angeles": {"civil": 1.36, "mechanical": 1.25, "electrical": 1.27, "labour": 1.49},
    "chicago":     {"civil": 1.30, "mechanical": 1.22, "electrical": 1.25, "labour": 1.43},
    "houston":     {"civil": 1.15, "mechanical": 1.11, "electrical": 1.13, "labour": 1.22},
    "dallas":      {"civil": 1.11, "mechanical": 1.09, "electrical": 1.10, "labour": 1.19},
    "atlanta":     {"civil": 1.09, "mechanical": 1.08, "electrical": 1.09, "labour": 1.15},
    "toronto":     {"civil": 1.20, "mechanical": 1.18, "electrical": 1.19, "labour": 1.24},
    "vancouver":   {"civil": 1.26, "mechanical": 1.21, "electrical": 1.24, "labour": 1.32},
    "montreal":    {"civil": 1.09, "mechanical": 1.12, "electrical": 1.13, "labour": 1.09},
    "mexico city": {"civil": 0.79, "mechanical": 0.79, "electrical": 0.79, "labour": 0.79},
    # Middle East / ASEAN
    "dubai":       {"civil": 1.13, "mechanical": 1.16, "electrical": 1.17, "labour": 0.91},
    "abu dhabi":   {"civil": 1.16, "mechanical": 1.17, "electrical": 1.18, "labour": 0.93},
    "riyadh":      {"civil": 1.04, "mechanical": 1.06, "electrical": 1.07, "labour": 0.81},
    "singapore":   {"civil": 1.30, "mechanical": 1.25, "electrical": 1.27, "labour": 1.36},
    "kuala lumpur":{"civil": 0.85, "mechanical": 0.84, "electrical": 0.85, "labour": 0.77},
    "jakarta":     {"civil": 0.80, "mechanical": 0.80, "electrical": 0.80, "labour": 0.72},
    "bangkok":     {"civil": 0.83, "mechanical": 0.83, "electrical": 0.84, "labour": 0.75},
    "shanghai":    {"civil": 0.98, "mechanical": 0.96, "electrical": 0.97, "labour": 0.93},
    "tokyo":       {"civil": 1.37, "mechanical": 1.34, "electrical": 1.37, "labour": 1.56},
    "hong kong":   {"civil": 1.36, "mechanical": 1.30, "electrical": 1.31, "labour": 1.53},
    # Oceania
    "sydney":      {"civil": 1.63, "mechanical": 1.63, "electrical": 1.63, "labour": 1.67},
    "melbourne":   {"civil": 1.60, "mechanical": 1.60, "electrical": 1.60, "labour": 1.63},
    # Africa / LatAm
    "cairo":       {"civil": 0.72, "mechanical": 0.72, "electrical": 0.72, "labour": 0.62},
    "johannesburg":{"civil": 0.88, "mechanical": 0.86, "electrical": 0.87, "labour": 0.84},
    "sao paulo":   {"civil": 1.14, "mechanical": 1.11, "electrical": 1.12, "labour": 1.16},
    "buenos aires":{"civil": 0.91, "mechanical": 0.91, "electrical": 0.91, "labour": 0.91},
}

NEUTRAL_CITY = {"civil": 1.00, "mechanical": 1.00, "electrical": 1.00, "labour": 1.00}


def city_factor_lookup(city_name: str) -> Dict[str, float]:
    """Case-insensitive city lookup with fallback to neutral 1.00."""
    if not city_name:
        return dict(NEUTRAL_CITY, matched=False, resolved=None)
    key = " ".join(city_name.strip().lower().split())
    if key in CITY_FACTORS:
        return dict(CITY_FACTORS[key], matched=True, resolved=key.title())
    for tok in key.split():
        if tok in CITY_FACTORS:
            return dict(CITY_FACTORS[tok], matched=True, resolved=tok.title())
    return dict(NEUTRAL_CITY, matched=False, resolved=None)


def get_benchmark_city_factors(country: str) -> Dict[str, float]:
    """Return raw city factors for a country's benchmark city."""
    bench = BENCHMARK_CITY.get(country)
    if bench and bench in CITY_FACTORS:
        return CITY_FACTORS[bench]
    return NEUTRAL_CITY'''
    
from typing import Dict, Any

# ───────────────────────────────────────────────────────────────
# USA BASE RATES (the 1.00x anchor)
# ───────────────────────────────────────────────────────────────
USA_BASE_CSA  = 650    # $/m² CSA at 1500 kg/m² floor load
USA_BASE_UTIL = 920    # $/m² utilities (full-length piping, all systems)

# ───────────────────────────────────────────────────────────────
# COUNTRY_COST_FACTORS (USA = 1.00)
# csa_factor  → × USA_BASE_CSA  = country CSA $/m² at @1500
# util_factor → × USA_BASE_UTIL = country utility $/m²
# others_pct  → % of (CSA+Util) for WH+ASRS, EPCM, Statutory, Staff
# ───────────────────────────────────────────────────────────────
COUNTRY_COST_FACTORS = {
    # ---- AMEA ----
    "India":            {"csa_factor": 0.612, "util_factor": 0.363, "others_pct": 0.649},
    "China":            {"csa_factor": 0.677, "util_factor": 0.457, "others_pct": 0.55},
    "UAE":              {"csa_factor": 0.815, "util_factor": 0.630, "others_pct": 0.65},
    "Saudi Arabia":     {"csa_factor": 0.769, "util_factor": 0.587, "others_pct": 0.60},
    "South Africa":     {"csa_factor": 0.585, "util_factor": 0.413, "others_pct": 0.55},
    "Egypt":            {"csa_factor": 0.492, "util_factor": 0.337, "others_pct": 0.50},
    "Thailand":         {"csa_factor": 0.554, "util_factor": 0.391, "others_pct": 0.53},
    "Vietnam":          {"csa_factor": 0.538, "util_factor": 0.370, "others_pct": 0.52},
    "Indonesia":        {"csa_factor": 0.531, "util_factor": 0.380, "others_pct": 0.52},
    "Australia":        {"csa_factor": 1.354, "util_factor": 1.000, "others_pct": 0.75},
    "New Zealand":      {"csa_factor": 1.292, "util_factor": 0.957, "others_pct": 0.73},
    "Japan":            {"csa_factor": 1.400, "util_factor": 1.100, "others_pct": 0.76},
    "South Korea":      {"csa_factor": 1.100, "util_factor": 0.870, "others_pct": 0.68},
    "Singapore":        {"csa_factor": 1.200, "util_factor": 0.960, "others_pct": 0.72},
    "Malaysia":         {"csa_factor": 0.620, "util_factor": 0.420, "others_pct": 0.53},
    "Philippines":      {"csa_factor": 0.500, "util_factor": 0.360, "others_pct": 0.50},
    "Bangladesh":       {"csa_factor": 0.440, "util_factor": 0.310, "others_pct": 0.48},
    "Pakistan":         {"csa_factor": 0.460, "util_factor": 0.320, "others_pct": 0.48},
    "Sri Lanka":        {"csa_factor": 0.480, "util_factor": 0.330, "others_pct": 0.49},
    # ---- MEU ----
    "Germany":          {"csa_factor": 1.308, "util_factor": 1.043, "others_pct": 0.75},
    "France":           {"csa_factor": 1.200, "util_factor": 1.000, "others_pct": 0.72},
    "UK":               {"csa_factor": 1.262, "util_factor": 0.978, "others_pct": 0.73},
    "Netherlands":      {"csa_factor": 1.292, "util_factor": 1.022, "others_pct": 0.74},
    "Belgium":          {"csa_factor": 1.260, "util_factor": 1.010, "others_pct": 0.73},
    "Switzerland":      {"csa_factor": 1.508, "util_factor": 1.196, "others_pct": 0.80},
    "Austria":          {"csa_factor": 1.280, "util_factor": 1.030, "others_pct": 0.74},
    "Poland":           {"csa_factor": 1.183, "util_factor": 0.879, "others_pct": 0.674},
    "Czech Republic":   {"csa_factor": 1.329, "util_factor": 0.879, "others_pct": 0.794},
    "Slovakia":         {"csa_factor": 1.150, "util_factor": 0.850, "others_pct": 0.66},
    "Hungary":          {"csa_factor": 1.100, "util_factor": 0.830, "others_pct": 0.65},
    "Romania":          {"csa_factor": 0.920, "util_factor": 0.700, "others_pct": 0.58},
    "Bulgaria":         {"csa_factor": 0.850, "util_factor": 0.650, "others_pct": 0.55},
    "Italy":            {"csa_factor": 0.954, "util_factor": 0.848, "others_pct": 0.68},
    "Spain":            {"csa_factor": 0.892, "util_factor": 0.783, "others_pct": 0.65},
    "Portugal":         {"csa_factor": 0.840, "util_factor": 0.740, "others_pct": 0.62},
    "Greece":           {"csa_factor": 0.880, "util_factor": 0.760, "others_pct": 0.63},
    "Turkey":           {"csa_factor": 0.720, "util_factor": 0.550, "others_pct": 0.55},
    "Norway":           {"csa_factor": 1.462, "util_factor": 1.174, "others_pct": 0.78},
    "Sweden":           {"csa_factor": 1.277, "util_factor": 1.043, "others_pct": 0.74},
    "Denmark":          {"csa_factor": 1.350, "util_factor": 1.080, "others_pct": 0.76},
    "Finland":          {"csa_factor": 1.300, "util_factor": 1.050, "others_pct": 0.75},
    "Ireland":          {"csa_factor": 1.240, "util_factor": 0.990, "others_pct": 0.72},
    # ---- North America ----
    "USA":              {"csa_factor": 1.000, "util_factor": 1.000, "others_pct": 0.72},
    "Canada":           {"csa_factor": 1.077, "util_factor": 1.043, "others_pct": 0.73},
    "Mexico":           {"csa_factor": 0.646, "util_factor": 0.457, "others_pct": 0.55},
    # ---- Latin America ----
    "Brazil":           {"csa_factor": 0.631, "util_factor": 0.435, "others_pct": 0.55},
    "Argentina":        {"csa_factor": 0.569, "util_factor": 0.391, "others_pct": 0.52},
    "Colombia":         {"csa_factor": 0.585, "util_factor": 0.402, "others_pct": 0.52},
    "Chile":            {"csa_factor": 0.662, "util_factor": 0.489, "others_pct": 0.55},
    "Peru":             {"csa_factor": 0.554, "util_factor": 0.380, "others_pct": 0.50},
    "Ecuador":          {"csa_factor": 0.520, "util_factor": 0.360, "others_pct": 0.50},
    "Uruguay":          {"csa_factor": 0.600, "util_factor": 0.420, "others_pct": 0.53},
    # ---- Africa ----
    "Nigeria":          {"csa_factor": 0.550, "util_factor": 0.400, "others_pct": 0.52},
    "Kenya":            {"csa_factor": 0.520, "util_factor": 0.380, "others_pct": 0.50},
    "Ghana":            {"csa_factor": 0.510, "util_factor": 0.370, "others_pct": 0.50},
    "Morocco":          {"csa_factor": 0.560, "util_factor": 0.400, "others_pct": 0.52},
    "Tunisia":          {"csa_factor": 0.540, "util_factor": 0.390, "others_pct": 0.51},
}


def get_country_cost_factors(country: str) -> Dict[str, float]:
    """Return csa_factor, util_factor, others_pct. Defaults to USA."""
    return COUNTRY_COST_FACTORS.get(country, COUNTRY_COST_FACTORS["USA"])



# Utility systems used by the estimator.
# (name, unit, base_rate_usd, discipline)
UTILITY_SYSTEMS = [
    ("Water Supply System",        "LS",  240200.00, "civil"),
    ("Steam & Boiler System",      "LS",  720012.00, "mechanical"),
    ("Refrigeration / Cold Chain", "LS",  901000.00, "mechanical"),
    ("Compressed Air System",     "LS",   40500.00, "mechanical"),
    ("Electrical Infrastructure", "LS", 1000005.00, "electrical"),
    ("HVAC",                       "LS",  400000.00, "civil"),
    ("Utility Piping",             "LS",  877500.00, "civil"),
    ("Fire Fighting System",       "LS",  500001.00, "mechanical"),
]


# Region -> country compatibility map.
# Numeric values reuse the existing country's csa_factor.
REGION_MULTIPLIERS = {
    "AMEA": {
        "India": 0.612, "China": 0.677, "UAE": 0.815, "Saudi Arabia": 0.769,
        "South Africa": 0.585, "Egypt": 0.492, "Thailand": 0.554, "Vietnam": 0.538,
        "Indonesia": 0.531, "Australia": 1.354, "New Zealand": 1.292, "Japan": 1.400,
        "South Korea": 1.100, "Singapore": 1.200, "Malaysia": 0.620,
        "Philippines": 0.500, "Bangladesh": 0.440, "Pakistan": 0.460, "Sri Lanka": 0.480,
    },
    "MEU": {
        "Germany": 1.308, "France": 1.200, "UK": 1.262, "Netherlands": 1.292,
        "Belgium": 1.260, "Switzerland": 1.508, "Austria": 1.280, "Poland": 1.183,
        "Czech Republic": 1.329, "Slovakia": 1.150, "Hungary": 1.100, "Romania": 0.920,
        "Bulgaria": 0.850, "Italy": 0.954, "Spain": 0.892, "Portugal": 0.840,
        "Greece": 0.880, "Turkey": 0.720, "Norway": 1.462, "Sweden": 1.277,
        "Denmark": 1.350, "Finland": 1.300, "Ireland": 1.240,
    },
    "North America": {"USA": 1.000, "Canada": 1.077, "Mexico": 0.646},
    "Latin America": {
        "Brazil": 0.631, "Argentina": 0.569, "Colombia": 0.585, "Chile": 0.662,
        "Peru": 0.554, "Ecuador": 0.520, "Uruguay": 0.600,
    },
    "Africa": {
        "Nigeria": 0.550, "Kenya": 0.520, "Ghana": 0.510, "Morocco": 0.560,
        "Tunisia": 0.540,
    },
}



# ───────────────────────────────────────────────────────────────
# UTILITY SYSTEM WEIGHTS (fraction of total utility cost)
# Sum = 1.00 — applied to (USA_BASE_UTIL × util_factor × built_up)
# ───────────────────────────────────────────────────────────────
UTILITY_SYSTEM_WEIGHTS = {
    "HVAC":                       (0.272, "mechanical",  "HVAC incl ductwork, AHUs, controls"),
    "Electrical Infrastructure":  (0.228, "electrical",  "HT/LT panels, transformers, cable trays"),
    "Utility Piping":             (0.113, "mechanical",  "HW 55/85C, chilled water, glycol, process"),
    "Steam & Boiler System":      (0.065, "mechanical",  "Steam header 10 bar, condensate, boiler"),
    "Refrigeration / Cold Chain": (0.098, "mechanical",  "Chillers, cooling towers, glycol loop"),
    "Fire Fighting System":       (0.092, "mechanical",  "Wet riser, sprinklers, hydrants, pump"),
    "Compressed Air System":      (0.033, "mechanical",  "Compressors, dryers, ring main 7 bar"),
    "Water Supply System":        (0.030, "civil",       "WTP, storage, distribution, softener"),
    "IT/OT System":               (0.035, "electrical",  "SCADA, MES, BMS, network backbone"),
    "Wastewater Treatment":       (0.034, "civil",       "WWTP, ETP, sludge handling"),
}

# ───────────────────────────────────────────────────────────────
# CIVIL ACTIVITIES — BOQ line items (USD, USA reference rates)
# ───────────────────────────────────────────────────────────────
CIVIL_ACTIVITIES = [
    ("Excavation",                     "m3",  28.00,   "Earthwork"),
    ("PCC (M10)",                      "m3",  120.00,  "Foundation"),
    ("RCC Foundation (Raft)",          "m3",  185.00,  "Foundation"),
    ("Structural Steel (PEB)",         "MT",  1300.00, "Superstructure"),
    ("RCC Superstructure",             "m3",  315.00,  "Superstructure"),
    ("Roofing (Insulated Panel)",      "m2",  39.00,   "Roofing"),
    ("Flooring (Epoxy + PU)",          "m2",  29.00,   "Finishing"),
    ("Walls (Block + Plaster + Tile)", "m2",  82.00,   "Finishing"),
    ("Plumbing & Sanitary",            "LS",  240200,  "MEP"),
    ("External Works & Roads",         "m2",  48.00,   "Infra"),
    ("Compound Wall / Fence",          "m",   145.00,  "Infra"),
    ("Landscaping",                    "m2",  4.74,    "Infra"),
]

# ───────────────────────────────────────────────────────────────
# LOCATION FACTOR
# ───────────────────────────────────────────────────────────────
LOCATION_FACTOR = {"Metro": 1.00, "Non-Metro": 0.92, "Remote": 1.10}

# ───────────────────────────────────────────────────────────────
# COMPLEXITY FACTORS
# ───────────────────────────────────────────────────────────────
COMPLEXITY_FACTORS = {
    "seismic_zone_high":      1.12,
    "high_humidity":          1.06,
    "cold_region":            1.08,
    "brownfield":             1.15,
    "gmp_hygienic":           1.18,     # benchmark default ON
    "explosion_risk":         1.10,
    "utility_redundancy":     1.15,     # benchmark default ON
    "remote_site":            1.12,
    "remote_location_civil":  1.10,
    "seismic_zone_moderate":  1.05,
    "height_over_12m":        1.08,
    "brownfield_civil":       1.12,
    "coastal_corrosion":      1.10,
}

# Benchmark = GMP(1.18) x Redundancy(1.15) = 1.357
BENCHMARK_COMPLEXITY_M = 1.357

# ───────────────────────────────────────────────────────────────
# BENCHMARK STRUCTURAL — the image reference scenario
# Raft+Hard+MedGWT+Zone2+Zone0+Steel+PEB+8m+24ms+1.2FAR+10.5m
# ───────────────────────────────────────────────────────────────
BENCHMARK_STRUCTURAL_M = 0.9440

# ───────────────────────────────────────────────────────────────
# PRODUCT CATEGORY → auto floor load (kN)
# ───────────────────────────────────────────────────────────────
PRODUCT_CATEGORY_LOAD = {
    "Chocolate Plant":          1500,
    "Bakery + Chocolate Combo": 1500,
    "Bakery":                    1000,
    "Warehouse":                 750,
    "_default":                 1000,
}

# ───────────────────────────────────────────────────────────────
# FLOOR LOAD MULTIPLIER — relative to @1500 (the csa_factor ref)
# csa_factor calibrated AT 1500. Lower loads get a discount.
# Image: India @1000=$318, @1500=$398 → 318/398=0.799
# ───────────────────────────────────────────────────────────────
FLOOR_LOAD_REL_1500 = {
    750: {
        "India": 0.666, "China": 0.670, "UAE": 0.680, "Saudi Arabia": 0.675,
        "South Africa": 0.667, "Egypt": 0.665, "Thailand": 0.667, "Vietnam": 0.665,
        "Indonesia": 0.665, "Australia": 0.690, "New Zealand": 0.688,
        "Germany": 0.690, "France": 0.688, "UK": 0.688, "Netherlands": 0.690,
        "Switzerland": 0.695, "Poland": 0.680, "Czech Republic": 0.686,
        "Italy": 0.685, "Spain": 0.683, "Norway": 0.693, "Sweden": 0.690,
        "USA": 0.690, "Canada": 0.690, "Mexico": 0.670,
        "Brazil": 0.670, "Argentina": 0.665, "Colombia": 0.665,
        "Chile": 0.672, "Peru": 0.665,
        "_default": 0.680,
    },
    1000: {
        "India": 0.799, "China": 0.805, "UAE": 0.815, "Saudi Arabia": 0.810,
        "South Africa": 0.800, "Egypt": 0.798, "Thailand": 0.800, "Vietnam": 0.798,
        "Indonesia": 0.798, "Australia": 0.828, "New Zealand": 0.825,
        "Germany": 0.828, "France": 0.825, "UK": 0.825, "Netherlands": 0.828,
        "Switzerland": 0.832, "Poland": 0.773, "Czech Republic": 0.771,
        "Italy": 0.818, "Spain": 0.815, "Norway": 0.830, "Sweden": 0.828,
        "USA": 0.828, "Canada": 0.828, "Mexico": 0.805,
        "Brazil": 0.805, "Argentina": 0.798, "Colombia": 0.798,
        "Chile": 0.808, "Peru": 0.798,
        "_default": 0.810,
    },
    1500: {"_default": 1.000},
}


def get_floor_load_multiplier(product_category: str, country: str) -> Dict[str, Any]:
    """Auto-assign floor load, return multiplier relative to @1500."""
    load_kg_m2 = PRODUCT_CATEGORY_LOAD.get(product_category, PRODUCT_CATEGORY_LOAD["_default"])
    valid = sorted(FLOOR_LOAD_REL_1500.keys())
    snapped = min(valid, key=lambda x: abs(x - load_kg_m2))
    table = FLOOR_LOAD_REL_1500[snapped]
    mult = table.get(country, table.get("_default", 1.0))
    return {"load_kg_m2": load_kg_m2, "snapped": snapped, "multiplier": round(mult, 4),
            "country": country, "product_category": product_category}


# ───────────────────────────────────────────────────────────────
# BENCHMARK CITY — per country (city_adj = 1.00 at benchmark)
# ───────────────────────────────────────────────────────────────
BENCHMARK_CITY = {
    "India":          "sricity",
    "Poland":         "plonsk",
    "Czech Republic": "opava",
    "USA":            "houston",
    "Germany":        "hamburg",
    "France":         "lyon",
    "UK":             "manchester",
    "China":          "shanghai",
    "Mexico":         "mexico city",
    "Brazil":         "sao paulo",
    "_default":       None,
}

# ───────────────────────────────────────────────────────────────
# EMPLOYEE FACILITY RATES (by country)
# ───────────────────────────────────────────────────────────────
EMPLOYEE_FACILITY_RATES = {
    "India":          {"civil_finish": 45,  "mep": 35,  "locker": 85,  "shoe_rack": 15, "bench": 40},
    "China":          {"civil_finish": 55,  "mep": 42,  "locker": 95,  "shoe_rack": 18, "bench": 48},
    "Thailand":       {"civil_finish": 48,  "mep": 38,  "locker": 88,  "shoe_rack": 16, "bench": 42},
    "Vietnam":        {"civil_finish": 42,  "mep": 33,  "locker": 80,  "shoe_rack": 14, "bench": 38},
    "Indonesia":      {"civil_finish": 44,  "mep": 34,  "locker": 82,  "shoe_rack": 14, "bench": 39},
    "Egypt":          {"civil_finish": 40,  "mep": 30,  "locker": 75,  "shoe_rack": 13, "bench": 35},
    "South Africa":   {"civil_finish": 52,  "mep": 40,  "locker": 95,  "shoe_rack": 17, "bench": 45},
    "UAE":            {"civil_finish": 85,  "mep": 70,  "locker": 165, "shoe_rack": 32, "bench": 80},
    "Saudi Arabia":   {"civil_finish": 78,  "mep": 62,  "locker": 150, "shoe_rack": 28, "bench": 72},
    "Australia":      {"civil_finish": 155, "mep": 130, "locker": 300, "shoe_rack": 52, "bench": 140},
    "New Zealand":    {"civil_finish": 140, "mep": 118, "locker": 275, "shoe_rack": 48, "bench": 128},
    "Poland":         {"civil_finish": 95,  "mep": 75,  "locker": 180, "shoe_rack": 30, "bench": 85},
    "Czech Republic": {"civil_finish": 105, "mep": 82,  "locker": 195, "shoe_rack": 35, "bench": 92},
    "Germany":        {"civil_finish": 145, "mep": 120, "locker": 280, "shoe_rack": 50, "bench": 130},
    "France":         {"civil_finish": 138, "mep": 115, "locker": 268, "shoe_rack": 48, "bench": 125},
    "UK":             {"civil_finish": 140, "mep": 115, "locker": 265, "shoe_rack": 48, "bench": 125},
    "Netherlands":    {"civil_finish": 148, "mep": 122, "locker": 285, "shoe_rack": 51, "bench": 132},
    "Switzerland":    {"civil_finish": 175, "mep": 145, "locker": 340, "shoe_rack": 60, "bench": 158},
    "Italy":          {"civil_finish": 118, "mep": 95,  "locker": 225, "shoe_rack": 40, "bench": 108},
    "Spain":          {"civil_finish": 108, "mep": 86,  "locker": 205, "shoe_rack": 37, "bench": 98},
    "Norway":         {"civil_finish": 180, "mep": 150, "locker": 350, "shoe_rack": 62, "bench": 165},
    "Sweden":         {"civil_finish": 155, "mep": 128, "locker": 298, "shoe_rack": 53, "bench": 138},
    "USA":            {"civil_finish": 165, "mep": 140, "locker": 320, "shoe_rack": 55, "bench": 150},
    "Canada":         {"civil_finish": 155, "mep": 130, "locker": 300, "shoe_rack": 52, "bench": 140},
    "Mexico":         {"civil_finish": 58,  "mep": 45,  "locker": 105, "shoe_rack": 20, "bench": 52},
    "Brazil":         {"civil_finish": 60,  "mep": 48,  "locker": 110, "shoe_rack": 21, "bench": 55},
    "Argentina":      {"civil_finish": 48,  "mep": 38,  "locker": 90,  "shoe_rack": 16, "bench": 42},
    "Colombia":       {"civil_finish": 50,  "mep": 40,  "locker": 92,  "shoe_rack": 17, "bench": 44},
    "Chile":          {"civil_finish": 68,  "mep": 55,  "locker": 128, "shoe_rack": 24, "bench": 62},
    "Peru":           {"civil_finish": 48,  "mep": 38,  "locker": 88,  "shoe_rack": 16, "bench": 42},
    "_default":       {"civil_finish": 85,  "mep": 68,  "locker": 160, "shoe_rack": 30, "bench": 75},
}


def get_employee_facility_rates(country: str) -> Dict[str, float]:
    return EMPLOYEE_FACILITY_RATES.get(country, EMPLOYEE_FACILITY_RATES["_default"])


# ───────────────────────────────────────────────────────────────
# INDUSTRY PRESETS
# ───────────────────────────────────────────────────────────────
INDUSTRY_PRESETS = {
    "Chocolate Plant":          {"utilities_pct": 0.63, "cold_chain_pct": 0.18, "hvac_pct": 0.11},
    "Bakery + Chocolate Combo": {"utilities_pct": 0.60, "cold_chain_pct": 0.16, "hvac_pct": 0.11},
    "Bakery":                   {"utilities_pct": 0.50, "cold_chain_pct": 0.05, "hvac_pct": 0.09},
    "Warehouse":                {"utilities_pct": 0.25, "cold_chain_pct": 0.02, "hvac_pct": 0.04},
}

COMPLIANCE_ADDER_PCT = 0.09
CONTINGENCY_PCT      = 0.08

CURRENCY_SYMBOLS = {
    "USD": "$", "EUR": "€", "GBP": "£", "INR": "₹", "JPY": "¥",
    "AUD": "A$", "CAD": "C$", "CHF": "CHF", "CNY": "¥", "SGD": "S$",
    "AED": "AED", "ZAR": "R", "BRL": "R$", "MXN": "Mex$", "CZK": "Kc",
    "PLN": "zl", "HUF": "Ft", "SEK": "kr", "NOK": "kr", "DKK": "kr",
}

# ───────────────────────────────────────────────────────────────
# CITY FACTORS — RAW discipline adjustments
# Normalized to benchmark city in compute_estimate()
# ───────────────────────────────────────────────────────────────
CITY_FACTORS = {
    # India
    "mumbai":      {"civil": 1.05, "mechanical": 0.97, "electrical": 0.98, "labour": 1.09},
    "navi mumbai": {"civil": 0.98, "mechanical": 0.93, "electrical": 0.95, "labour": 1.01},
    "delhi":       {"civil": 1.01, "mechanical": 0.95, "electrical": 0.97, "labour": 1.05},
    "gurgaon":     {"civil": 1.03, "mechanical": 0.97, "electrical": 0.98, "labour": 1.06},
    "noida":       {"civil": 0.98, "mechanical": 0.93, "electrical": 0.95, "labour": 1.01},
    "bangalore":   {"civil": 0.97, "mechanical": 0.93, "electrical": 0.95, "labour": 1.01},
    "chennai":     {"civil": 0.90, "mechanical": 0.89, "electrical": 0.90, "labour": 0.93},
    "hyderabad":   {"civil": 0.89, "mechanical": 0.87, "electrical": 0.89, "labour": 0.90},
    "pune":        {"civil": 0.93, "mechanical": 0.90, "electrical": 0.92, "labour": 0.95},
    "kolkata":     {"civil": 0.77, "mechanical": 0.79, "electrical": 0.83, "labour": 0.72},
    "ahmedabad":   {"civil": 0.81, "mechanical": 0.82, "electrical": 0.83, "labour": 0.77},
    "sricity":     {"civil": 0.82, "mechanical": 0.84, "electrical": 0.85, "labour": 0.80},
    "sri city":     {"civil": 0.82, "mechanical": 0.84, "electrical": 0.85, "labour": 0.80},
    
    "bhubaneswar": {"civil": 0.70, "mechanical": 0.73, "electrical": 0.74, "labour": 0.58},
    "indore":      {"civil": 0.71, "mechanical": 0.74, "electrical": 0.75, "labour": 0.63},
    "coimbatore":  {"civil": 0.75, "mechanical": 0.77, "electrical": 0.78, "labour": 0.68},
    "kochi":       {"civil": 0.77, "mechanical": 0.80, "electrical": 0.81, "labour": 0.72},
    "jaipur":      {"civil": 0.74, "mechanical": 0.77, "electrical": 0.77, "labour": 0.66},
    "lucknow":     {"civil": 0.71, "mechanical": 0.74, "electrical": 0.75, "labour": 0.63},
    # Europe
    "opava":       {"civil": 0.74, "mechanical": 0.74, "electrical": 0.74, "labour": 0.74},
    "prague":      {"civil": 0.77, "mechanical": 0.77, "electrical": 0.77, "labour": 0.77},
    "brno":        {"civil": 0.75, "mechanical": 0.75, "electrical": 0.75, "labour": 0.75},
    "plonsk":      {"civil": 0.72, "mechanical": 0.72, "electrical": 0.72, "labour": 0.72},
    "warsaw":      {"civil": 0.75, "mechanical": 0.75, "electrical": 0.75, "labour": 0.75},
    "krakow":      {"civil": 0.73, "mechanical": 0.73, "electrical": 0.73, "labour": 0.73},
    "wroclaw":     {"civil": 0.72, "mechanical": 0.72, "electrical": 0.72, "labour": 0.72},
    "gdansk":      {"civil": 0.71, "mechanical": 0.71, "electrical": 0.71, "labour": 0.71},
    "berlin":      {"civil": 1.01, "mechanical": 1.01, "electrical": 1.01, "labour": 1.01},
    "munich":      {"civil": 1.12, "mechanical": 1.07, "electrical": 1.08, "labour": 1.17},
    "hamburg":     {"civil": 1.05, "mechanical": 1.03, "electrical": 1.03, "labour": 1.07},
    "frankfurt":   {"civil": 1.08, "mechanical": 1.05, "electrical": 1.06, "labour": 1.12},
    "paris":       {"civil": 1.12, "mechanical": 1.06, "electrical": 1.08, "labour": 1.18},
    "lyon":        {"civil": 1.02, "mechanical": 1.01, "electrical": 1.02, "labour": 1.05},
    "london":      {"civil": 1.27, "mechanical": 1.15, "electrical": 1.17, "labour": 1.37},
    "manchester":  {"civil": 1.08, "mechanical": 1.03, "electrical": 1.06, "labour": 1.10},
    "amsterdam":   {"civil": 1.11, "mechanical": 1.07, "electrical": 1.09, "labour": 1.15},
    "milan":       {"civil": 0.98, "mechanical": 0.96, "electrical": 0.97, "labour": 1.01},
    "rome":        {"civil": 0.95, "mechanical": 0.95, "electrical": 0.96, "labour": 0.98},
    "madrid":      {"civil": 0.89, "mechanical": 0.89, "electrical": 0.89, "labour": 0.89},
    "barcelona":   {"civil": 0.90, "mechanical": 0.90, "electrical": 0.90, "labour": 0.91},
    # North America
    "new york":    {"civil": 1.43, "mechanical": 1.30, "electrical": 1.33, "labour": 1.59},
    "los angeles": {"civil": 1.36, "mechanical": 1.25, "electrical": 1.27, "labour": 1.49},
    "chicago":     {"civil": 1.30, "mechanical": 1.22, "electrical": 1.25, "labour": 1.43},
    "houston":     {"civil": 1.15, "mechanical": 1.11, "electrical": 1.13, "labour": 1.22},
    "dallas":      {"civil": 1.11, "mechanical": 1.09, "electrical": 1.10, "labour": 1.19},
    "atlanta":     {"civil": 1.09, "mechanical": 1.08, "electrical": 1.09, "labour": 1.15},
    "toronto":     {"civil": 1.20, "mechanical": 1.18, "electrical": 1.19, "labour": 1.24},
    "vancouver":   {"civil": 1.26, "mechanical": 1.21, "electrical": 1.24, "labour": 1.32},
    "montreal":    {"civil": 1.09, "mechanical": 1.12, "electrical": 1.13, "labour": 1.09},
    "mexico city": {"civil": 0.79, "mechanical": 0.79, "electrical": 0.79, "labour": 0.79},
    # Middle East / ASEAN
    "dubai":       {"civil": 1.13, "mechanical": 1.16, "electrical": 1.17, "labour": 0.91},
    "abu dhabi":   {"civil": 1.16, "mechanical": 1.17, "electrical": 1.18, "labour": 0.93},
    "riyadh":      {"civil": 1.04, "mechanical": 1.06, "electrical": 1.07, "labour": 0.81},
    "singapore":   {"civil": 1.30, "mechanical": 1.25, "electrical": 1.27, "labour": 1.36},
    "kuala lumpur":{"civil": 0.85, "mechanical": 0.84, "electrical": 0.85, "labour": 0.77},
    "jakarta":     {"civil": 0.80, "mechanical": 0.80, "electrical": 0.80, "labour": 0.72},
    "bangkok":     {"civil": 0.83, "mechanical": 0.83, "electrical": 0.84, "labour": 0.75},
    "shanghai":    {"civil": 0.98, "mechanical": 0.96, "electrical": 0.97, "labour": 0.93},
    "tokyo":       {"civil": 1.37, "mechanical": 1.34, "electrical": 1.37, "labour": 1.56},
    "hong kong":   {"civil": 1.36, "mechanical": 1.30, "electrical": 1.31, "labour": 1.53},
    # Oceania
    "sydney":      {"civil": 1.63, "mechanical": 1.63, "electrical": 1.63, "labour": 1.67},
    "melbourne":   {"civil": 1.60, "mechanical": 1.60, "electrical": 1.60, "labour": 1.63},
    # Africa / LatAm
    "cairo":       {"civil": 0.72, "mechanical": 0.72, "electrical": 0.72, "labour": 0.62},
    "johannesburg":{"civil": 0.88, "mechanical": 0.86, "electrical": 0.87, "labour": 0.84},
    "sao paulo":   {"civil": 1.14, "mechanical": 1.11, "electrical": 1.12, "labour": 1.16},
    "buenos aires":{"civil": 0.91, "mechanical": 0.91, "electrical": 0.91, "labour": 0.91},
}

NEUTRAL_CITY = {"civil": 1.00, "mechanical": 1.00, "electrical": 1.00, "labour": 1.00}


def city_factor_lookup(city_name: str) -> Dict[str, float]:
    """Case-insensitive city lookup with fallback to neutral 1.00."""
    if not city_name:
        return dict(NEUTRAL_CITY, matched=False, resolved=None)
    key = " ".join(city_name.strip().lower().split())
    if key in CITY_FACTORS:
        return dict(CITY_FACTORS[key], matched=True, resolved=key.title())
    for tok in key.split():
        if tok in CITY_FACTORS:
            return dict(CITY_FACTORS[tok], matched=True, resolved=tok.title())
    return dict(NEUTRAL_CITY, matched=False, resolved=None)


def get_benchmark_city_factors(country: str) -> Dict[str, float]:
    """Return raw city factors for a country's benchmark city."""
    bench = BENCHMARK_CITY.get(country)
    if bench and bench in CITY_FACTORS:
        return CITY_FACTORS[bench]
    return NEUTRAL_CITY

