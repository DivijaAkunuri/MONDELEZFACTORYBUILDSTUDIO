
"""
Static city -> country -> region mapping for Construction Estimator.
No geocoding API or internet connection is required.
Country names match COUNTRY_COST_FACTORS in rate_data.py.
"""

# Every city below is taken from the latest CITY_FACTORS table.
# Format: city: (country, region)

CITY_TO_COUNTRY_REGION = {
    # INDIA
    "mumbai": ("India", "AMEA"),
    "navi mumbai": ("India", "AMEA"),
    "delhi": ("India", "AMEA"),
    "gurgaon": ("India", "AMEA"),
    "noida": ("India", "AMEA"),
    "bangalore": ("India", "AMEA"),
    "bengaluru": ("India", "AMEA"),
    "chennai": ("India", "AMEA"),
    "hyderabad": ("India", "AMEA"),
    "pune": ("India", "AMEA"),
    "kolkata": ("India", "AMEA"),
    "ahmedabad": ("India", "AMEA"),
    "sricity": ("India", "AMEA"),
    "sri city": ("India", "AMEA"),
    "bhubaneswar": ("India", "AMEA"),
    "indore": ("India", "AMEA"),
    "coimbatore": ("India", "AMEA"),
    "kochi": ("India", "AMEA"),
    "jaipur": ("India", "AMEA"),
    "lucknow": ("India", "AMEA"),

    # EUROPE - CZECH REPUBLIC
    "opava": ("Czech Republic", "MEU"),
    "prague": ("Czech Republic", "MEU"),
    "brno": ("Czech Republic", "MEU"),

    # EUROPE - POLAND
    "plonsk": ("Poland", "MEU"),
    "warsaw": ("Poland", "MEU"),
    "krakow": ("Poland", "MEU"),
    "wroclaw": ("Poland", "MEU"),
    "gdansk": ("Poland", "MEU"),

    # EUROPE - GERMANY
    "berlin": ("Germany", "MEU"),
    "munich": ("Germany", "MEU"),
    "hamburg": ("Germany", "MEU"),
    "frankfurt": ("Germany", "MEU"),

    # EUROPE - FRANCE
    "paris": ("France", "MEU"),
    "lyon": ("France", "MEU"),

    # EUROPE - UNITED KINGDOM
    "london": ("UK", "MEU"),
    "manchester": ("UK", "MEU"),

    # EUROPE - NETHERLANDS
    "amsterdam": ("Netherlands", "MEU"),

    # EUROPE - ITALY
    "milan": ("Italy", "MEU"),
    "rome": ("Italy", "MEU"),

    # EUROPE - SPAIN
    "madrid": ("Spain", "MEU"),
    "barcelona": ("Spain", "MEU"),

    # NORTH AMERICA - USA
    "new york": ("USA", "North America"),
    "los angeles": ("USA", "North America"),
    "chicago": ("USA", "North America"),
    "houston": ("USA", "North America"),
    "dallas": ("USA", "North America"),
    "atlanta": ("USA", "North America"),

    # NORTH AMERICA - CANADA
    "toronto": ("Canada", "North America"),
    "vancouver": ("Canada", "North America"),
    "montreal": ("Canada", "North America"),

    # NORTH AMERICA - MEXICO
    "mexico city": ("Mexico", "North America"),

    # MIDDLE EAST
    "dubai": ("UAE", "AMEA"),
    "abu dhabi": ("UAE", "AMEA"),
    "riyadh": ("Saudi Arabia", "AMEA"),

    # ASIA / ASEAN
    "singapore": ("Singapore", "AMEA"),
    "kuala lumpur": ("Malaysia", "AMEA"),
    "jakarta": ("Indonesia", "AMEA"),
    "bangkok": ("Thailand", "AMEA"),
    "shanghai": ("China", "AMEA"),
    "tokyo": ("Japan", "AMEA"),
    "hong kong": ("China", "AMEA"),

    # OCEANIA
    "sydney": ("Australia", "AMEA"),
    "melbourne": ("Australia", "AMEA"),

    # AFRICA
    "cairo": ("Egypt", "AMEA"),
    "johannesburg": ("South Africa", "AMEA"),

    # LATIN AMERICA
    "sao paulo": ("Brazil", "Latin America"),
    "buenos aires": ("Argentina", "Latin America"),
}


# Alternative spellings and commonly used city names
CITY_ALIASES = {
    "new delhi": "delhi",
    "gurugram": "gurgaon",
    "bangalore city": "bangalore",
    "bengaluru city": "bengaluru",
    "sri-city": "sri city",
    "sri city chittoor": "sri city",
    "cochin": "kochi",
    "bombay": "mumbai",
    "madras": "chennai",
    "calcutta": "kolkata",
    "baroda": "vadodara",
}


def normalize_city(city: str) -> str:
    """Normalize city input and resolve known aliases."""
    if not city:
        return ""

    key = " ".join(city.strip().casefold().split())
    return CITY_ALIASES.get(key, key)


def lookup_city_location(city: str):
    """
    Return the city, country and region.
    Returns None if the city is not in the database.
    """
    key = normalize_city(city)

    if key not in CITY_TO_COUNTRY_REGION:
        return None

    country, region = CITY_TO_COUNTRY_REGION[key]

    return {
        "city": key.title(),
        "country": country,
        "region": region,
    }
