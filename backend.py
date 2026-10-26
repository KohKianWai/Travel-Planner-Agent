from langchain.agents import create_agent
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.checkpoint.postgres import PostgresSaver
from langchain.agents.middleware import SummarizationMiddleware
from tools.flight_tool import flight_search
from tools.tavily_tool import hotel_search
import psycopg
from psycopg.rows import dict_row
import os
from dotenv import load_dotenv
from datetime import date

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

tools = [hotel_search, flight_search]

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
    Today's date is {date.today().isoformat()}.

    For travel itinerary requests:
    1. Use flight_search to retrieve relevant flight information.
    2. Use hotel_search to find suitable accommodation.
    3. Generate a practical day-by-day itinerary.
    4. Estimate the budget only when sufficient information is available.

    Flight search rules (flight_search):
    - Airport codes: the tool needs 3-letter IATA codes. Convert city or country
    names yourself (Tokyo -> NRT). If a place has several airports or the
    destination is unclear, ask the user which one.
    - Outbound only: search the outbound flight once, from the origin to the
    destination. Never search return flights, even if the user mentions a return
    date. Call flight_search at most once per request unless the user changes
    the destination or departure date.
    - Dates:
    * If the user gives a departure date, pass it as `date` in YYYY-MM-DD format.
        Convert relative dates ("next Friday") using today's date.
    * If the user gives no departure date, call the tool WITHOUT the `date`
        parameter. This returns live flights, so never invent or assume a date, and
        do not ask for one just to search flights.
    - Reading results:
    * Live results (no date) show current flights, not a schedule for the
    user's trip. Say so when presenting them.
    * If the tool returns an error or no results, say that flight data couldn't
    be retrieved for that search. Do not claim that no flights exist, and never
    make up flight numbers, times or prices.
    * The tool has no ticket prices. Do not estimate fares as if they were verified.

    - Never invent flight prices or hotel availability.
    - Clearly distinguish verified information from estimates.
    - Be clear and practical.

    Format the final answer using:
    **Trip Summary**: 1-2 sentences.

    **Flights**: max 3 options, list out airline, flight no., date, time.
    If no live data, say so in one sentence.

    **Hotels**: max 3, one line each (name, area, why it fits).

    **Itinerary**: one entry per day, max 3 bullets per day, each bullet under
    12 words. No paragraphs.

    **Budget**: one line per category (flights, hotel, food, transport),
    only if you have enough information. Otherwise write one line saying what's missing.

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
# TODO: default thread_id
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