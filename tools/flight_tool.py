import os

import re
import certifi
import airportsdata
import pycountry
from dotenv import load_dotenv
from langchain.tools import tool
import requests
from datetime import date as date_cls, datetime

load_dotenv()

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

AVIATIONSTACK_API_KEY = os.getenv("AVIATIONSTACK_API_KEY")


LIVE_FLIGHT_URL = "https://api.aviationstack.com/v1/flights"
FUTURE_FLIGHT_URL = "https://api.aviationstack.com/v1/flightsFuture"

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

def format_future_flight(f: dict) -> str:
    dep, arr = f.get("departure") or {}, f.get("arrival") or {}
    airline = (f.get("airline") or {}).get("name") or "Unknown airline"
    fl = f.get("flight") or {}
    number = fl.get("iataNumber") or fl.get("iata") or "N/A"
    return (
        f"{airline} {number} | scheduled\n"
        f"  Depart: {dep.get('iataCode', '?')} {dep.get('scheduledTime', 'N/A')}, "
        f"Terminal {dep.get('terminal') or 'N/A'}, Gate {dep.get('gate') or 'N/A'}\n"
        f"  Arrive: {arr.get('iataCode', '?')} {arr.get('scheduledTime', 'N/A')}"
    )

def api_call(url: str, params: dict):
    try:
        data = requests.get(url, params=params, timeout=30).json()
    except requests.exceptions.RequestException as e:
        return None, f"Flight API request failed: {e}"
    except ValueError:
        return None, "Flight API returned invalid JSON."
    if "error" in data:
        err = data["error"]

        if isinstance(err, dict):
            message = err.get("message", "Unknown error")
        else:
            message = str(err)

        return None, f"Flight API error: {message}"

    return data.get("data") or [], None


@tool
def flight_search(destination: str, origin: str = "KUL", date: str | None = None) -> str:
    """Search flight schedules and status between two airports.
    Returns airline, flight number, times, terminals, gates and delays.
    Does NOT return ticket prices.

    Args:
        destination (str): 3-letter IATA code of the arrival airport, e.g. "NRT".
        origin (str): 3-letter IATA code of the departure airport. Defaults to "KUL".
        date (str): Departure date as YYYY-MM-DD. Only set this if the user
            explicitly stated a departure date. Leave empty otherwise to get
            live flights.
    """
    if not AVIATIONSTACK_API_KEY:
        return "Flight API error: AVIATIONSTACK_API_KEY is missing."
        
    origin, destination = origin.strip().upper(), destination.strip().upper()
    if not (origin.isalpha() and len(origin) == 3 and destination.isalpha() and len(destination) == 3):
        return "Invalid IATA code. Use 3-letter airport codes."


    # No date: live flights
    if not date:
        params = {
            "access_key": AVIATIONSTACK_API_KEY,
            "limit": 3,
            "dep_iata": origin,
            "arr_iata": destination
        }
        flights, err = api_call(LIVE_FLIGHT_URL, params)
        if err:
            return err
        if not flights:
            return f"No flight data found for route {origin} to {destination}."
        header = f"Live flights {origin} -> {destination} ({len(flights)} results):"
        return header + "\n\n" + "\n\n".join(format_flight(f) for f in flights)

    # Dated search
    try:
        travel_date = datetime.strptime(date.strip(), "%Y-%m-%d").date()
    except ValueError:
        return "Invalid date. Use YYYY-MM-DD, e.g. 2026-11-20."

    if travel_date <= date_cls.today():
        return "Travel date cannot be in the past."

    params = {
        "access_key": AVIATIONSTACK_API_KEY,
        "iataCode": origin, 
        "type": "departure",
        "date": travel_date.isoformat(), 
        "limit": 100
    }

    flights_data, err = api_call(FUTURE_FLIGHT_URL, params)

    if err:
        return err

    matches = [f for f in flights_data if str((f.get("arrival") or {}).get("iataCode", "")).upper() == destination][:3]

    if not matches:
        return (f"No scheduled flights found for {origin} to {destination} on {travel_date}. "
                "This may mean the schedule isn't available yet, not that no flights exist.")
    
    header = f"Scheduled flights {origin} -> {destination} on {travel_date} ({len(matches)} results):"
    return header + "\n\n" + "\n\n".join(format_future_flight(f) for f in matches)

    


