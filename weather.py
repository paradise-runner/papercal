import requests
import random
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta


def geocode_location(location: str) -> Optional[Tuple[float, float]]:
    """
    Geocode a location string to get latitude and longitude
    Uses Open-Meteo's geocoding API
    Returns (latitude, longitude) tuple or None if not found
    """
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": location, "count": 1, "language": "en", "format": "json"}

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("results") and len(data["results"]) > 0:
            result = data["results"][0]
            return (result["latitude"], result["longitude"])
        else:
            print(f"Location '{location}' not found")
            return None
    except Exception as e:
        print(f"Error geocoding location '{location}': {e}")
        return None


def get_weather_data(latitude: float = None, longitude: float = None) -> List[Dict]:
    """
    Fetch weather data from Open-Meteo API
    Returns a list of daily weather data for the current week
    If latitude/longitude not provided, defaults to Fort Collins, CO
    """
    # Default to Fort Collins, CO coordinates if not provided
    if latitude is None:
        latitude = 40.5853
    if longitude is None:
        longitude = -105.0844

    # Get current date and calculate week range
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())  # Monday
    end_of_week = start_of_week + timedelta(days=6)  # Sunday

    # Format dates for API
    start_date = start_of_week.strftime("%Y-%m-%d")
    end_date = end_of_week.strftime("%Y-%m-%d")

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "temperature_2m_max,temperature_2m_min,weathercode",
        "timezone": "America/Denver",
        "start_date": start_date,
        "end_date": end_date,
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        daily_data = data["daily"]
        weather_days = []

        for i in range(len(daily_data["time"])):
            date = daily_data["time"][i]
            weather_days.append(
                {
                    "date": date,
                    "temp_max": daily_data["temperature_2m_max"][i],
                    "temp_min": daily_data["temperature_2m_min"][i],
                    "weather_code": daily_data["weathercode"][i],
                    "icon": get_weather_icon(daily_data["weathercode"][i], date),
                }
            )

        return weather_days
    except Exception as e:
        print(f"Error fetching weather data: {e}")
        # Return default weather data for the week
        return get_default_weather_data()


def get_weather_icon(weather_code: int, date: str = None) -> str:
    """
    Map weather codes to weather icon filenames
    Uses deterministic selection based on date to ensure consistency
    """
    # Open-Meteo weather codes mapping
    # https://open-meteo.com/en/docs

    # Available icons
    icons = [
        "sun.svg",
        "cloudy.svg",
        "cloud-sun.svg",
        "umbrella.svg",
        "snowflake.svg",
        "wind.svg",
        "zap.svg",
        "haze.svg",
    ]

    # Use date as seed for deterministic selection
    if date:
        # Simple hash of date to get consistent index
        seed = sum(ord(c) for c in date) % 1000
        random.seed(seed)

    if weather_code in [0, 1]:  # Clear sky, mainly clear
        result = "sun.svg"
    elif weather_code in [2]:  # Partly cloudy
        result = "cloud-sun.svg"
    elif weather_code in [3]:  # overcast
        result = "cloudy.svg"
    elif weather_code in [45, 48]:  # Fog
        result = "haze.svg"
    elif weather_code in [51, 53, 55, 56, 57]:  # Drizzle
        result = "umbrella.svg"
    elif weather_code in [61, 63, 65, 66, 67]:  # Rain
        result = "umbrella.svg"
    elif weather_code in [71, 73, 75, 77, 85, 86]:  # Snow
        result = "snowflake.svg"
    elif weather_code in [80, 81, 82]:  # Rain showers
        result = "umbrella.svg"
    elif weather_code in [95, 96, 99]:  # Thunderstorm
        result = "zap.svg"
    else:
        # Default to deterministic icon for unknown codes
        result = random.choice(icons)

    # Reset random seed to avoid affecting other random operations
    random.seed()
    return result


def get_default_weather_data() -> List[Dict]:
    """
    Return default weather data when API is unavailable
    """
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())

    default_data = []
    icons = [
        "sun.svg",
        "cloudy.svg",
        "cloud-sun.svg",
        "umbrella.svg",
        "snowflake.svg",
        "wind.svg",
        "zap.svg",
    ]

    for i in range(7):
        date = start_of_week + timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        default_data.append(
            {
                "date": date_str,
                "temp_max": random.randint(60, 80),
                "temp_min": random.randint(40, 60),
                "weather_code": 1,  # Mainly clear
                "icon": get_weather_icon(1, date_str),
            }
        )

    return default_data
