import httpx
from rate_data import REGION_MULTIPLIERS


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"

# Match Open-Meteo country names to the names used by rate_data.py.
COUNTRY_ALIASES = {
    "United States": "USA",
    "United States of America": "USA",
    "United Kingdom": "UK",
    "Czechia": "Czech Republic",
    "United Arab Emirates": "UAE",
}

# Countries outside the estimator's current cost database
# will be assigned to "Other".
def get_estimator_region(country: str) -> str:
    country = COUNTRY_ALIASES.get(country, country)

    for region, countries in REGION_MULTIPLIERS.items():
        if country in countries:
            return region

    return "Other"


def normalize_country(country: str) -> str:
    return COUNTRY_ALIASES.get(country, country)


async def lookup_city_location(city: str):
    """
    Search worldwide cities using Open-Meteo Geocoding API.

    Returns a list of locations containing:
    city, country, country_code, region, state and formatted.
    """

    if not city or not city.strip():
        return []

    params = {
        "name": city.strip(),
        "count": 10,
        "language": "en",
        "format": "json",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            GEOCODING_URL,
            params=params,
        )
        response.raise_for_status()
        data = response.json()

    results = data.get("results", []) or []
    locations = []

    for item in results:
        city_name = item.get("name")
        country_name = item.get("country")

        if not city_name or not country_name:
            continue

        country_name = normalize_country(country_name)
        state = item.get("admin1") or ""

        region = get_estimator_region(country_name)

        formatted_parts = [city_name]

        if state and state.casefold() != city_name.casefold():
            formatted_parts.append(state)

        formatted_parts.append(country_name)

        locations.append({
            "city": city_name,
            "country": country_name,
            "country_code": item.get("country_code", ""),
            "region": region,
            "state": state,
            "formatted": ", ".join(formatted_parts),
            "latitude": item.get("latitude"),
            "longitude": item.get("longitude"),
        })

    return locations