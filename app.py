from typing import Optional

from flask import Flask, render_template, request
import requests

app = Flask(__name__)

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
}


def lookup_city(city: str) -> Optional[dict]:
    response = requests.get(
        GEOCODE_URL,
        params={"name": city, "count": 1},
        timeout=10,
    )
    response.raise_for_status()
    results = response.json().get("results") or []
    return results[0] if results else None


def fetch_weather(lat: float, lon: float) -> dict:
    response = requests.get(
        WEATHER_URL,
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
        },
        timeout=10,
    )
    response.raise_for_status()
    return response.json()["current"]


@app.route("/", methods=["GET", "POST"])
def index():
    weather = None
    error = None
    city = ""

    if request.method == "POST":
        city = (request.form.get("city") or "").strip()
        if not city:
            error = "Please enter a city name."
        else:
            try:
                place = lookup_city(city)
                if not place:
                    error = f'No match found for "{city}".'
                else:
                    current = fetch_weather(place["latitude"], place["longitude"])
                    weather = {
                        "city": place["name"],
                        "country": place.get("country", ""),
                        "temperature": current["temperature_2m"],
                        "humidity": current["relative_humidity_2m"],
                        "wind": current["wind_speed_10m"],
                        "description": WEATHER_CODES.get(
                            current["weather_code"], "Unknown conditions"
                        ),
                    }
            except requests.RequestException:
                error = "Could not reach the weather service. Try again."

    return render_template("index.html", weather=weather, error=error, city=city)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
