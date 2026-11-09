import json
import logging
from pathlib import Path
from typing import Any

import httpx
from rate_data import REGION_MULTIPLIERS


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FALLBACK_FILE = Path(__file__).with_name("missing_city_locations.json")


COUNTRY_ALIASES = {
    "United States": "USA",
    "United States of America": "USA",
    "United Kingdom": "UK",
    "Czechia": "Czech Republic",
    "United Arab Emirates": "UAE",
    "Türkiye": "Turkey",
    "Republic of Türkiye": "Turkey",
}


def _normal(value: Any) -> str:
    return " ".join(str(value or "").casefold().strip().split())


def normalize_country(country: str) -> str:
    country = str(country or "").strip()

    for original, alias in COUNTRY_ALIASES.items():
        if _normal(country) == _normal(original):
            return alias

    return country


def get_estimator_region(country: str) -> str:
    country = normalize_country(country)

    for region, countries in REGION_MULTIPLIERS.items():
        if country in countries:
            return region

    return "Other"


def load_fallback_cities():
    try:
        with FALLBACK_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)

        return data if isinstance(data, list) else []

    except FileNotFoundError:
        logging.warning("Fallback city file not found: %s", FALLBACK_FILE)
        return []

    except (json.JSONDecodeError, OSError):
        logging.exception("Could not load fallback city file")
        return []


FALLBACK_CITIES = load_fallback_cities()


def format_location(city: str, state: str, country: str) -> str:
    parts = [city]

    if state and _normal(state) != _normal(city):
        parts.append(state)

    if country:
        parts.append(country)

    return ", ".join(parts)


async def search_open_meteo(client, search_name):
    response = await client.get(
        GEOCODING_URL,
        params={
            "name": search_name,
            "count": 10,
            "language": "en",
            "format": "json",
        },
    )

    response.raise_for_status()
    return response.json().get("results", []) or []


async def lookup_city_location(city: str):
    """
    Search worldwide cities using Open-Meteo.

    Also checks the supplementary fallback file for the
    17 locations that were not found in the original test.
    """

    query = str(city or "").strip()

    if len(query) < 2:
        return []

    locations = []
    seen = set()

    async with httpx.AsyncClient(timeout=20.0) as client:

        # 1. Normal worldwide Open-Meteo search
        try:
            api_results = await search_open_meteo(client, query)
        except httpx.HTTPError:
            logging.exception("Worldwide geocoding search failed")
            api_results = []

        for item in api_results:
            city_name = str(item.get("name") or "").strip()
            country_name = normalize_country(item.get("country") or "")

            if not city_name or not country_name:
                continue

            state = str(item.get("admin1") or "").strip()

            key = (
                _normal(city_name),
                _normal(country_name),
                _normal(state),
            )

            if key in seen:
                continue

            seen.add(key)

            locations.append({
                "city": city_name,
                "country": country_name,
                "country_code": item.get("country_code", ""),
                "region": get_estimator_region(country_name),
                "state": state,
                "formatted": format_location(
                    city_name, state, country_name
                ),
                "latitude": item.get("latitude"),
                "longitude": item.get("longitude"),
                "source": "open_meteo",
            })

        # 2. Search supplementary fallback entries
        for fallback in FALLBACK_CITIES:

            original_city = str(fallback.get("city") or "").strip()
            country = normalize_country(fallback.get("country") or "")
            state = str(fallback.get("state") or "").strip()

            lookup_queries = fallback.get("lookup_queries", [])

            searchable_names = [original_city] + lookup_queries

            # Only process fallback entries related to the user's query
            if not any(
                _normal(query) in _normal(name)
                or _normal(name) in _normal(query)
                for name in searchable_names
                if name
            ):
                continue

            for search_name in lookup_queries:

                try:
                    fallback_results = await search_open_meteo(
                        client, search_name
                    )
                except httpx.HTTPError:
                    logging.warning(
                        "Fallback search failed for %s",
                        search_name,
                    )
                    continue

                # Accept only results from the expected country
                matching_results = [
                    item for item in fallback_results
                    if _normal(
                        normalize_country(item.get("country") or "")
                    ) == _normal(country)
                ]

                if not matching_results:
                    continue

                item = matching_results[0]

                latitude = item.get("latitude")
                longitude = item.get("longitude")

                if latitude is None or longitude is None:
                    continue

                key = (
                    _normal(original_city),
                    _normal(country),
                    str(latitude),
                    str(longitude),
                )

                if key in seen:
                    continue

                seen.add(key)

                locations.append({
                    "city": original_city,
                    "country": country,
                    "country_code": item.get("country_code", ""),
                    "region": get_estimator_region(country),
                    "state": state,
                    "formatted": format_location(
                        original_city, state, country
                    ),
                    "latitude": latitude,
                    "longitude": longitude,
                    "source": "fallback_database",
                })

                # One successful alternate match is enough for this entry
                break

    return locations