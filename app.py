from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from backend import run_agent
from pydantic import BaseModel


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class UserRequest(BaseModel):
    message: str
    thread_id: str | None = None

@app.post("/api/travel")
def travel_planner(request: UserRequest):
    try:
        user_message = request.message.strip()

        if not user_message:
            raise HTTPException(status_code=400, detail="Message cannot be empty.")

        if not request.thread_id:
            raise HTTPException(status_code=400, detail="No thread id provided.")

        result = run_agent(user_message, request.thread_id)
        return {"answer": result["answer"]}

    except Exception as e:
        raise HTTPException(status_code=500, detail="Something went wrong. Please try again.")