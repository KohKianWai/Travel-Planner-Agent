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

    For travel itinerary requests:
    1. Use flight_search to retrieve relevant flight information.
    2. Use hotel_search to find suitable accommodation.
    3. Generate a practical day-by-day itinerary.
    4. Estimate the budget only when sufficient information is available.

    Flight search rules (flight_search):
    - Airport codes: the tool needs 3-letter IATA codes. Convert city or country
    names yourself (Tokyo -> NRT). If a place has several airports or the
    destination is unclear, ask the user which one.
    - flight_search only returns live/recent flights, not future schedules or prices.
    If it returns no results, say that live data wasn't available. Do not claim
    that no flights exist.
    - If the user's request is missing key details (destination, number of
    days), ask before planning.
    - flight_search only returns outbound flights
    - User could not request for a specific flights
    - Never invent flight prices or hotel availability.
    - Clearly distinguish verified information from estimates.
    - Be clear and practical.

    Important Rules:
    - Use Malaysian currency.

    Format the final answer using:
    **Trip Summary**: 1-2 sentences.

    **Flights**: max 3 options, list out airline, flight no., departure, arrival date and time.
    If no live data, say so in one sentence.

    **Hotels**: max 3, one line each (name, area, why it fits).

    **Itinerary**: one entry per day, max 3 bullets per day, each bullet under
    12 words. No paragraphs.

    **Budget**: one line per category: hotel, food, local transport and
    activities. Give estimates only when you have enough information (number of
    days, destination, budget level); otherwise write one line saying what's
    missing. Do not include flights in the budget. End with this exact note:
    "Flight prices are not available, so they are not included in this budget."
    Include the total budget.

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