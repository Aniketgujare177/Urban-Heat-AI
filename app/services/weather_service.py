import requests


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def get_location_weather(latitude, longitude):

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "apparent_temperature,"
            "wind_speed_10m,"
            "weather_code"
        ),
        "timezone": "Asia/Kolkata"
    }

    try:
        response = requests.get(
            OPEN_METEO_URL,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()
        current = data["current"]

        return {
            "temperature": current["temperature_2m"],
            "humidity": current["relative_humidity_2m"],
            "feels_like": current["apparent_temperature"],
            "wind_speed": current["wind_speed_10m"],
            "weather_code": current["weather_code"],
            "time": current["time"],
            "source": "Open-Meteo",
            "is_live": True
        }

    except (
        requests.RequestException,
        KeyError,
        TypeError,
        ValueError
    ):

        return {
            "temperature": None,
            "humidity": None,
            "feels_like": None,
            "wind_speed": None,
            "weather_code": None,
            "time": None,
            "source": "Unavailable",
            "is_live": False
        }