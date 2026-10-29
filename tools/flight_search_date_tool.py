import os
from apify_client import ApifyClient
from dotenv import load_dotenv
from langchain.tools import tool
from datetime import datetime, timedelta

apify = ApifyClient(os.getenv("APIFY_API_TOKEN"))
ACTOR_ID = "makework36/flight-price-scraper"

def format_time(iso: str | None) -> str:
    """'2019-12-12T04:20:00+00:00' -> '12 Dec 04:20'"""
    if not iso:
        return "N/A"
    try:
        return datetime.fromisoformat(iso).strftime("%d %b %H:%M")
    except ValueError:
        return iso

def format_flight(f: dict) -> str:
    airline = f.get("airline") or "Unknown airline"
    price = f.get("bestPrice")
    price_text = f"{f.get('currency', '')} {price}" if price is not None else "price N/A"
    return (
        f"Airline: {airline}\n"
        f"Flight code: {f.get("flightCode", 'N/A')}\n"
        f"Price: {price_text}\n"
        f"Duration: {f.get('duration', 'N/A')}\n"
        f"Depart: {format_time(f.get("departTime", ''))}\n"
        f"Arrive: {format_time(f.get("arriveTime", ''))}\n"
    )

@tool
def flight_search_date(destination: str, depart_date: str, origin: str = "KUL",
                        return_date: str | None = None) -> str:
    """Search flight schedule and prices for a specific date. All prices listed are on a per-individual basis.

    Args:
        destination (str): 3-letter IATA code of the arrival airport, e.g. "NRT".
        depart_date (str): Departure date as YYYY-MM-DD.
        origin (str): 3-letter IATA code of the departure airport, e.g. "KUL".
        return_date (str): Optional return date as YYYY-MM-DD for a round trip.
    """
    origin, destination = origin.strip().upper(), destination.strip().upper()
    if not (origin.isalpha() and len(origin) == 3 and destination.isalpha() and len(destination) == 3):
        return "Invalid IATA code. Use 3-letter airport codes."

    
    params = {
        "origin": origin, 
        "destination": destination, 
        "departDate": depart_date,
        "adults": 1, 
        "cabinClass": "ECONOMY", 
        "currency": "MYR", 
        "maxFlights": 3,
    }
    if return_date:
        params["returnDate"] = return_date
    try:
        run = apify.actor(ACTOR_ID).call(
            run_input=params, 
            run_timeout=timedelta(seconds=90), 
            wait_duration=timedelta(seconds=90)
        )
        if not run or run.status != "SUCCEEDED":
            return "Flight search failed."
        items = list(apify.dataset(run.default_dataset_id).iterate_items())
    except Exception as e:
        return f"Flight price search failed: {e}"

    if not items:
        return f"No priced flights found for {origin} to {destination} on {depart_date}."

    items = items[:3]
    header = f"Indicative prices {origin} -> {destination} on {depart_date} ({len(items)} results):"
    return header + "\n\n" + "\n\n".join(format_flight(f) for f in items)