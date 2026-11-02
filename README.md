# Travel Planner Agent

An AI-powered travel planning assistant that helps users organize their trips through natural language conversations. Users can provide their destination, travel dates, trip duration, and budget to receive personalized travel recommendations.

## Features

- **AI-Powered Travel Assistance:** Understands natural language requests and supports conversational trip planning.
- **Flight Search:** Retrieves flight schedules and available flight information based on the user's travel requirements.
- **Hotel Search:** Searches for hotels and accommodation options based on the destination and preferences.
- **Itinerary Generation:** Creates day-by-day travel itineraries with suggested activities and attractions.
- **Budget Estimation:** Provides estimated travel expenses across categories such as flights, accommodation, food, transportation, and activities.
- **Conversational Memory:** Maintains conversation context to support follow-up questions and itinerary modifications.

## Project structure

```
└── travel-planner-agent/
    ├── .env
    ├── docker-compose.yml
    ├── README.md
    ├── requirements.txt
    ├── travel-ui/
    │   ├── Dockerfile
    │   ├── index.html
    │   └── src/
    │       ├── App.jsx
    │       ├── ChatPage.jsx
    │       ├── index.css
    │       ├── main.css
    │       └── main.jsx
    └── backend/
        ├── app.py
        ├── backend.py
        ├── Dockerfile
        └── tools/
            ├── flight_search_date_tool.py
            ├── flight_search_live_tool.py
            └── tavily_tool.py
```

## Prerequisites

- Python 3.12+
- Node.js 22+ (for local frontend development)
- Docker and Docker Compose (optional)
- A PostgreSQL database (for example a Render Postgres instance)
- API keys for the services below

| Service | Used for | Variable |
|---|---|---|
| [Groq](https://console.groq.com) | LLM | `GROQ_API_KEY` |
| [Tavily](https://tavily.com) | Hotel search | `TAVILY_API_KEY` |
| [AviationStack](https://aviationstack.com) | Live flight status | `AVIATIONSTACK_API_KEY` |
| [Apify](https://apify.com) | Flight prices for specific dates | `APIFY_API_TOKEN` |
| PostgreSQL | Conversation memory | `DATABASE_URL` |

## Configuration

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_key
TAVILY_API_KEY=your_tavily_key
AVIATIONSTACK_API_KEY=your_aviationstack_key
APIFY_API_TOKEN=your_apify_token
DATABASE_URL=postgresql://user:password@host:5432/dbname?sslmode=require

# Optional: LangSmith tracing and monitoring
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=travel-planner-agent
```

## Run locally

**Backend**

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cd backend
uvicorn app:app --reload --port 8000
```

**Frontend**

```bash
cd travel-ui
npm install
npm run dev
```

Open `http://localhost:5173`. Set the API address in `travel-ui/.env` if the backend isn't on port 8000:

```env
VITE_API_URL=http://localhost:8000
```

## Run with Docker

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |

Useful commands:

```bash
docker compose up -d              # run in the background
docker compose logs -f backend    # follow backend logs
docker compose down               # stop and remove containers
```

## Limitations

- **Flight prices are indicative.** They come from a scraper and can differ from the booking price.
- **Cannot book.** The agent presents options only.
- **Rate Limits.** Uses Groq's API, which is subject to rate limits on requests and token usage depending on the selected model and account tier.


