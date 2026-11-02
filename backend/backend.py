from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.checkpoint.postgres import PostgresSaver
from langchain.agents.middleware import SummarizationMiddleware
from tools.flight_search_live_tool import flight_search_live
from tools.flight_search_date_tool import flight_search_date
from tools.tavily_tool import hotel_search
import psycopg
from psycopg.rows import dict_row
import os
from dotenv import load_dotenv

load_dotenv()

def get_database_url():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise ValueError(
            "DATABASE_URL is missing. Please add your Render PostgreSQL External Database URL to .env"
        )

    return database_url

# ==============
# LLM
# ==============

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
    max_tokens=2000,
)

# ==============
# Tools
# ==============

tools = [hotel_search, flight_search_live, flight_search_date]

# ========================
# PostgreSQL Checkpointer
# ========================

DATABASE_URL = get_database_url()

_conn = psycopg.connect(
    DATABASE_URL,
    autocommit=True,
    row_factory=dict_row
)

checkpointer = PostgresSaver(_conn)
checkpointer.setup()

# ==============
# System Prompt
# ==============

SYSTEM_PROMPT = f"""
    You are a professional AI travel planning assistant.

    For travel itinerary requests:
    1. Use flight_search to retrieve relevant flight information.
    2. Use hotel_search to find suitable accommodation.
    3. Generate a practical day-by-day itinerary.
    4. Estimate the budget only when sufficient information is available.

    Flight search rules:

    Choosing the tool
    - You have two flight tools. Pick one based on whether the user gave a
    departure date:
    * User gave a departure date -> flight_search_date. Pass it as
        depart_date in YYYY-MM-DD format. Convert relative dates ("next Friday")
        using today's date.
    * User gave a departure and return date -> flight_search_date. Pass those as
        depart_date and return_date in YYYY-MM-DD format. Convert relative dates ("next Friday")
        using today's date.
    * User gave no date -> flight_search_live. This shows flights operating now,
        with no prices. Do not ask the user for a date just to search flights, and
        never invent or assume one.
    - Call at most one flight tool per request, once. Search again only if the user
    changes the destination or departure date.

    Airport codes
    - Both tools need 3-letter IATA codes. Convert city or country names yourself
    (Tokyo -> NRT). If a place has several airports or the destination is unclear,
    ask the user which one.

    - You cannot book flights or choose a specific flight for the user. Present
    options only.

    Reading results
    - flight_search_date: show up to 3 flights, one line each with airline, price,
    departure and arrival time.
    - flight_search_live: these are flights operating now, not a schedule for the
    user's trip. Say so, and state that prices are not available.
    - If a tool returns an error, a timeout or no results, say flight data couldn't
    be retrieved for that search and do not call another flight tool to retry. Do
    not claim that no flights exist. Never invent flight numbers, times or prices.

    Budget
    - Include flights in the budget only when flight_search_date returned a price.
    Otherwise add the note: "Flight prices are not available, so they are not
    included in this budget."

    General
    - If the destination or number of days is missing, ask before planning. Missing
    dates are not a reason to ask.
    - Never invent flight prices or hotel availability. Clearly distinguish verified
    information from estimates.

    Important Rules:
    - Use Malaysian currency.

    Format the final answer using:
    **Trip Summary**: 1-2 sentences.

    **Flights**: max 3 options, list out airline, flight no., departure, arrival date and time.
    If no live data, say so in one sentence.

    **Hotels**: max 3, one line each (name, area, why it fits).

    **Itinerary**: one entry per day, max 3 bullets per day, each bullet under
    12 words. No paragraphs.

    **Budget**: one line per category: hotel, flight, food, local transport and
    activities. Give estimates only when you have enough information (number of
    days, destination, budget level); otherwise write one line saying what's
    missing. Include the total budget.

    - For follow-up requests that modify an existing trip, begin the response
    with a brief sentence summarizing what changed, e.g., "Here is your
    revised trip with a 5-day itinerary and cheaper hotels."

    The whole answer should fit in roughly 400 words. For trips longer than 5 days,
    use one line per day.
    """

# ==============
# Agent
# ==============

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=SYSTEM_PROMPT,
    checkpointer=checkpointer,
    middleware=[
        SummarizationMiddleware(
            model=llm,
            trigger=("tokens", 4000),
            keep=("messages", 3),
        )
    ]
)

# ==============
# Trigger Function
# ==============

def run_agent(user_input: str, thread_id: str = "1") -> dict:
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }

    result = agent.invoke(
        {
            "messages": [
                HumanMessage(content=user_input)
            ]
        },
        config=config,
    )

    final_answer = result["messages"][-1].content

    return {
        "thread_id": thread_id,
        "answer": final_answer,
    }