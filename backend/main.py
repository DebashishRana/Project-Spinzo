from fastapi import FastAPI
import json
from pathlib import Path
from engine import DeductionEngine
from llm_layer import LLMLayer

app = FastAPI()


def load_players(path=None):
    if path is None:
        path = Path(__file__).resolve().parent / "players.json"
    else:
        path = Path(path)

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict) and "players" in data:
        players = data["players"]
    elif isinstance(data, list):
        players = data
    else:
        raise ValueError("players.json must contain a JSON array or a root object with a 'players' list.")

    if not isinstance(players, list):
        raise ValueError("players.json must contain a JSON array of player objects.")

    return players


PLAYERS_DATA = load_players()

@app.get("/")
def read_root():
    return {"message": "Akinator IPL Deduction Engine Backend Initialized."}

@app.post("/api/game/init")
def init_game():
    """Starts a new game and selects the first optimal question"""
    engine = DeductionEngine(PLAYERS_DATA)
    llm = LLMLayer()

    best_feature = engine.get_best_feature()
    question = llm.feature_to_question(best_feature)

    return {
        "status": "success",
        "feature": best_feature,
        "question": question
    }

@app.post("/api/game/answer")
def process_answer(feature: str, current_value: str, user_text: str):
    """Processes natural language answer, updates probabilities, and returns next step."""
    engine = DeductionEngine(PLAYERS_DATA)
    llm = LLMLayer()

    interpreted_answer = llm.parse_user_response(user_text)
    engine.update_probabilities(feature, current_value, interpreted_answer)

    top_candidates = engine.get_top_candidates()
    best_candidate, prob = top_candidates[0]

    if prob >= 0.85:
        return {
            "status": "complete",
            "prediction": best_candidate["name"],
            "confidence": prob
        }

    next_feature = engine.get_best_feature()
    next_question = llm.feature_to_question(next_feature)

    return {
        "status": "ongoing",
        "feature": next_feature,
        "question": next_question,
        "interpreted_answer": interpreted_answer,
        "top_current_prediction": best_candidate["name"]
    }
