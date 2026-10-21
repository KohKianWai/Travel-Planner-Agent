import os

from tavily import TavilyClient
from dotenv import load_dotenv
from langchain.tools import tool

load_dotenv()

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

@tool
def hotel_search(query: str) -> str:
    """Search the web for hotels, accommodation options,
    locations, and published price information.

    Args:
        query (str): Search query describing the destination, hotel preferences, or accommodation requirements.
    """

    response = tavily_client.search(
        query,
        max_results=3
    )

    results = []

    for i, r in enumerate(response.get("results", []), 1):
        title = r.get("title", "Unknown")
        url = r.get("url", "")
        content = (r.get("content") or "").strip()

        if len(content) > 300:
            content = content[:300].rsplit(" ", 1)[0] + "..."

        results.append(
            f"{i}. **{title}**\n"
            f"   URL: {url}\n"
            f"   Content: {content}"
        )

    return "\n\n".join(results) if results else "No results found."