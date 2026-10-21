import os

import re
import certifi
import airportsdata
import pycountry
from dotenv import load_dotenv
from langchain.tools import tool
import requests
from datetime import datetime

load_dotenv()

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

AVIATIONSTACK_API_KEY = os.getenv("AVIATIONSTACK_API_KEY")


BASE_URL = "https://api.aviationstack.com/v1/flights"

AIRPORTS = airportsdata.load("IATA")

def format_time(iso: str | None) -> str:
    """'2019-12-12T04:20:00+00:00' -> '12 Dec 04:20'"""
    if not iso:
        return "N/A"
    try:
        return datetime.fromisoformat(iso).strftime("%d %b %H:%M")
    except ValueError:
        return iso

def format_delay(minutes) -> str:
    return f"{minutes} min delay" if minutes else "on time"

def format_flight(f: dict) -> str:
    dep = f.get("departure") or {}
    arr = f.get("arrival") or {}

    airline = (f.get("airline") or {}).get("name") or "Unknown airline"
    flight_number = (f.get("flight") or {}).get("iata") or "N/A"
    aircraft = (f.get("aircraft") or {}).get("iata")
    status = f.get("flight_status") or "unknown"

    dep_airport = dep.get("airport") or "N/A"
    dep_iata = dep.get("iata") or "N/A"
    dep_terminal = dep.get("terminal") or "N/A"
    dep_gate = dep.get("gate") or "N/A"
    dep_scheduled = format_time(dep.get("scheduled"))
    dep_delay_text = format_delay(dep.get("delay"))

    arr_airport = arr.get("airport") or "N/A"
    arr_iata = arr.get("iata") or "N/A"
    arr_terminal = arr.get("terminal") or "N/A"
    arr_gate = arr.get("gate") or "N/A"
    arr_scheduled = format_time(arr.get("scheduled"))
    arr_delay_text = format_delay(arr.get("delay"))

    aircraft_text = f"\nAircraft: {aircraft}" if aircraft else ""

    return f"""
        Airline: {airline}
        Flight: {flight_number}
        Status: {status}

        Departure:
        - Airport: {dep_airport}
        - IATA: {dep_iata}
        - Terminal: {dep_terminal}
        - Gate: {dep_gate}
        - Scheduled: {dep_scheduled}
        - Delay: {dep_delay_text}

        Arrival:
        - Airport: {arr_airport}
        - IATA: {arr_iata}
        - Terminal: {arr_terminal}
        - Gate: {arr_gate}
        - Scheduled: {arr_scheduled}
        - Delay: {arr_delay_text}{aircraft_text}
        """.strip()

@tool
def flight_search(destination: str, origin: str = "KUL") -> str:
    """Search live flight schedules and status between two airports.
    Returns airline, flight number, times, terminals, gates and delays.
    Does NOT return ticket prices.

    Args:
        destination (str): 3-letter IATA code of the arrival airport, e.g. "NRT".
        origin (str): 3-letter IATA code of the departure airport. Defaults to "KUL".
    """
    if not AVIATIONSTACK_API_KEY:
        return "Flight API error: AVIATIONSTACK_API_KEY is missing."
        
    origin, destination = origin.strip().upper(), destination.strip().upper()
    if not (origin.isalpha() and len(origin) == 3 and destination.isalpha() and len(destination) == 3):
        return "Invalid IATA code. Use 3-letter airport codes."

    params = {
        "access_key": AVIATIONSTACK_API_KEY,
        "limit": 10,
        "dep_iata": origin,
        "arr_iata": destination
    }

    try:
        response = requests.get(BASE_URL, params=params, timeout=30)
        data = response.json()
    except requests.exceptions.RequestException as e:
        return f"Flight API request failed: {e}"
    except ValueError:
        return "Flight API returned invalid JSON."

    if "error" in data:
        err = data["error"]
        return f"Flight API error: {err.get('message', 'Unknown error')}"

    flight_data = data.get("data", [])

    if not flight_data:
        return f"No flight data found for route {origin} to {destination}."

    header = f"Live flights {origin} -> {destination} ({len(flight_data)} results):"
    return header + "\n\n" + "\n\n".join(format_flight(f) for f in flight_data)

    


