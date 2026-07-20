"""Static rate database derived from MDLZ cost evaluation and estimator framework.
All base rates are in USD per unit.  Regional multipliers adjust for location.
"""

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

# Utilities systems - fixed lump sum rates by capacity tiers
UTILITY_SYSTEMS = [
    ("Water Supply System", "LS", 920000.00),
    ("Steam & Boiler System", "LS", 1620000.00),
    ("Refrigeration / Cold Chain", "LS", 2450000.00),
    ("Compressed Air System", "LS", 780000.00),
    ("Electrical Infrastructure", "LS", 1980000.00),
    ("ETP / STP System", "LS", 950000.00),
    ("Fire Fighting System", "LS", 450000.00),
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
