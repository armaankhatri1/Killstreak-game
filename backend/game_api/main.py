from fastapi import FastAPI, HTTPException
from fastapi import status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import json
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can lock this down if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Setup ----------

SESSION_DIR = os.path.join(os.path.dirname(__file__), "sessions")
LEADERBOARD_FILE = os.path.join(os.path.dirname(__file__), "leaderboard.json")

os.makedirs(SESSION_DIR, exist_ok=True)

# If leaderboard.json doesn't exist, create it
if not os.path.exists(LEADERBOARD_FILE):
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump([], f)


# ---------- Request Models ----------

class StartRequest(BaseModel):
    player_id: str

class ShotData(BaseModel):
    session_id: str
    hit: bool
    reaction_time: float

class EndGame(BaseModel):
    session_id: str


# ---------- Helper Functions ----------

def get_session_path(session_id):
    return os.path.join(SESSION_DIR, f"{session_id}.json")

def load_session(session_id):
    path = get_session_path(session_id)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Session not found.")
    with open(path, "r") as f:
        return json.load(f)

def save_session(session_id, data):
    path = get_session_path(session_id)
    print(f"Saving session to: {path}")  # ✅ useful debug print
    with open(path, "w") as f:
        json.dump(data, f)


# ---------- Routes ----------

@app.post("/start")
def start_game(request: StartRequest):
    session_id = str(uuid.uuid4())
    session_data = {
        "player_id": request.player_id,
        "shots": [],
        "score": 0
    }
    save_session(session_id, session_data)
    return {"message": "Game started", "session_id": session_id}

@app.post("/shot")
def register_shot(data: ShotData):
    session = load_session(data.session_id)
    session["shots"].append({
        "hit": data.hit,
        "reaction_time": data.reaction_time
    })

    if data.hit:
        session["score"] += 1

    save_session(data.session_id, session)
    return {"message": "Shot recorded", "score": session["score"]}

@app.post("/end")
def end_game(data: EndGame):
    session = load_session(data.session_id)
    total_shots = len(session["shots"])
    avg_reaction_time = (
        sum(s["reaction_time"] for s in session["shots"]) / total_shots
        if total_shots > 0 else 0
    )

    # Load current leaderboard
    with open(LEADERBOARD_FILE, "r") as f:
        leaderboard = json.load(f)

    # Add new result
    leaderboard.append({
        "player_id": session["player_id"],
        "score": session["score"],
        "avg_reaction_time": avg_reaction_time
    })

    # Sort and trim to top 10
    leaderboard.sort(key=lambda x: (-x["score"], x["avg_reaction_time"]))
    leaderboard = leaderboard[:10]

    # Save updated leaderboard
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump(leaderboard, f, indent=4)

    # Delete the session file
    os.remove(get_session_path(data.session_id))

    return {
        "message": "Game ended",
        "player_id": session["player_id"],
        "score": session["score"],
        "total_shots": total_shots,
        "avg_reaction_time": round(avg_reaction_time, 2)
    }

@app.get("/leaderboard")
def get_leaderboard():
    with open(LEADERBOARD_FILE, "r") as f:
        leaderboard = json.load(f)
    return {"leaderboard": leaderboard}

@app.post("/reset-leaderboard", status_code=status.HTTP_204_NO_CONTENT)
def reset_leaderboard():
    with open(LEADERBOARD_FILE, "w") as f:
        json.dump([], f)

@app.post("/reset-sessions", status_code=status.HTTP_204_NO_CONTENT)
def reset_sessions():
    for filename in os.listdir(SESSION_DIR):
        file_path = os.path.join(SESSION_DIR, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
