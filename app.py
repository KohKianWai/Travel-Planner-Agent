from fastapi import FastAPI, HTTPException
from backend import run_agent
from pydantic import BaseModel

app = FastAPI()

class UserRequest(BaseModel):
    message: str
    thread_id: str

@app.post("/api/travel")
def travel_planner(request: UserRequest):
    try:
        user_message = request.message.strip()

        if not user_message:
            raise HTTPException(status_code=400, detail="Message cannot be empty.")

        result = run_agent(user_message, request.thread_id)
        return {"answer": result["answer"]}

    except Exception as e:
        raise HTTPException(status_code=500, detail="Something went wrong. Please try again.")