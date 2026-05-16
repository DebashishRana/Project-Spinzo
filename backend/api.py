"""
FastAPI backend for SPINZO IPL Akinator game.
Persists anonymous game sessions and feedback in Firestore.
"""

import os
import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.database import (
    FirestoreUnavailable,
    add_doc,
    get_doc,
    get_firestore_client,
    increment,
    list_docs,
    server_timestamp,
    set_doc,
)
from question import (
    ask_next_question,
    calculate_confidence,
    compute_field_splits,
    filter_players,
    get_candidate_fields,
    load_players,
    summarize_candidates,
)

app = FastAPI(title="SPINZO IPL Oracle", version="1.1")


def _cors_origins() -> List[str]:
    configured = os.getenv("ALLOWED_ORIGINS", "*").strip()
    if configured == "*":
        return ["*"]
    return [origin.strip() for origin in configured.split(",") if origin.strip()]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PUBLIC_INDEX = Path(__file__).resolve().parent.parent / "public" / "index.html"


@app.get("/", include_in_schema=False)
async def serve_frontend():
    """Serve the browser game when deployed as a single Render web service."""
    if not PUBLIC_INDEX.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    return FileResponse(PUBLIC_INDEX)

PLAYERS = load_players()
TOTAL_PLAYERS = len(PLAYERS)
CANDIDATE_FIELDS = get_candidate_fields()
PLAYER_BY_ID = {str(player.get("player_id") or player.get("short_name")): player for player in PLAYERS}
ALL_PLAYER_IDS = list(PLAYER_BY_ID.keys())


class GameStartRequest(BaseModel):
    """Request for starting a new game."""


class GameAnswerRequest(BaseModel):
    """Request for submitting an answer."""

    game_id: str
    answer: str


class GameFeedbackRequest(BaseModel):
    """Request for submitting final guess feedback."""

    game_id: str
    was_correct: bool
    guessed_player: Optional[str] = None
    actual_player: Optional[str] = None
    confidence: Optional[int] = None


class QuestionResponse(BaseModel):
    """Response with a new question."""

    game_id: str
    action: str = "question"
    question: str
    reaction: str
    thinkingMsg: str = ""
    confidence: int
    remaining_count: int
    question_number: int


class GuessResponse(BaseModel):
    """Response with a player guess."""

    game_id: str
    action: str = "guess"
    playerName: str
    playerTeam: str
    playerEmoji: str
    confidence: int
    guessReason: str


def _firestore_error(exc: FirestoreUnavailable) -> HTTPException:
    return HTTPException(status_code=503, detail=str(exc))


def _normalize_answer(answer: str) -> str:
    value = answer.strip().lower()
    if value in {"yes", "y"}:
        return "yes"
    if value in {"no", "n"}:
        return "no"
    if value in {"maybe", "probably", "unknown", "dont_know", "don't know", "idk"}:
        return "unknown"
    raise HTTPException(status_code=400, detail="Answer must be yes, no, maybe, or unknown.")


def _players_from_ids(player_ids: List[str]) -> List[Dict[str, Any]]:
    return [PLAYER_BY_ID[player_id] for player_id in player_ids if player_id in PLAYER_BY_ID]


def _player_id(player: Dict[str, Any]) -> str:
    return str(player.get("player_id") or player.get("short_name"))


def _safe_key(value: str) -> str:
    key = re.sub(r"[^a-zA-Z0-9_-]+", "_", value.strip().lower()).strip("_")
    return key or "unknown"


def _field_doc_id(field: str) -> str:
    return f"field_{_safe_key(field)}"


def _player_doc_id(player_name: str) -> str:
    return f"player_{_safe_key(player_name)}"


def _load_learning_stats() -> Dict[str, Dict[str, Any]]:
    try:
        return list_docs("learning_stats")
    except Exception:
        return {}


def _weighted_field_splits(
    remaining_players: List[Dict[str, Any]],
    asked_questions: List[Dict[str, Any]],
    learning_stats: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    field_splits = compute_field_splits(remaining_players, CANDIDATE_FIELDS, asked_questions)
    for split in field_splits:
        stats = learning_stats.get(_field_doc_id(split["field"]), {})
        correct = int(stats.get("correct_count", 0) or 0)
        wrong = int(stats.get("wrong_count", 0) or 0)
        total = correct + wrong
        if total:
            usefulness = (correct + 1) / (total + 2)
            multiplier = 0.85 + (usefulness * 0.30)
        else:
            multiplier = 1.0
        split["learning_multiplier"] = round(multiplier, 4)
        split["learned_entropy"] = round(split["entropy"] * multiplier, 4)

    field_splits.sort(key=lambda item: item["learned_entropy"], reverse=True)
    return field_splits


def _rank_players_by_learning(
    players: List[Dict[str, Any]],
    learning_stats: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    def learning_score(player: Dict[str, Any]) -> float:
        name = player.get("short_name") or player.get("full_name") or ""
        stats = learning_stats.get(_player_doc_id(name), {})
        correct = int(stats.get("correct_count", 0) or 0)
        wrong = int(stats.get("wrong_count", 0) or 0)
        total = correct + wrong
        if not total:
            return 1.0
        return 1.0 + max(min((correct - wrong) / (total + 2), 1.0), -1.0) * 0.15

    return sorted(players, key=learning_score, reverse=True)


def _fallback_question() -> Dict[str, str]:
    return {
        "question": "Is your player an all-rounder?",
        "reaction": "The oracle awakens...",
        "thinkingMsg": "Consulting IPL archives...",
        "targets_field": "identity.is_allrounder",
    }


def _build_guess(game_id: str, player: Dict[str, Any], confidence: float) -> GuessResponse:
    player_name = player.get("short_name", "Unknown")
    team = player.get("ipl_career", {}).get("primary_franchise") or "IPL Team"
    return GuessResponse(
        game_id=game_id,
        action="guess",
        playerName=player_name,
        playerTeam=team,
        playerEmoji="BAT",
        confidence=min(int(confidence * 100), 99),
        guessReason=f"Based on your answers, I'm confident this is {player_name}!",
    )


def _save_current_guess(game_id: str, guess: GuessResponse, remaining: List[Dict[str, Any]]) -> None:
    set_doc(
        "game_sessions",
        game_id,
        {
            "status": "guessed",
            "current_guess": guess.model_dump(),
            "final_candidate_ids": [_player_id(player) for player in remaining[:10]],
            "updated_at": server_timestamp(),
        },
    )


def _record_turn(game_id: str, turn_data: Dict[str, Any]) -> None:
    add_doc(
        "game_turns",
        {
            "game_id": game_id,
            **turn_data,
            "created_at": server_timestamp(),
        },
    )


def _update_learning_stats(
    session: Dict[str, Any],
    was_correct: bool,
    guessed_player: Optional[str],
    actual_player: Optional[str],
) -> None:
    count_field = "correct_count" if was_correct else "wrong_count"
    for item in session.get("history", []):
        field = item.get("field")
        if not field:
            continue
        set_doc(
            "learning_stats",
            _field_doc_id(field),
            {
                "category": "field",
                "field": field,
                count_field: increment(1),
                "total_count": increment(1),
                "updated_at": server_timestamp(),
            },
        )

    if guessed_player:
        set_doc(
            "learning_stats",
            _player_doc_id(guessed_player),
            {
                "category": "player",
                "player_name": guessed_player,
                count_field: increment(1),
                "total_count": increment(1),
                "updated_at": server_timestamp(),
            },
        )

    if not was_correct and actual_player:
        set_doc(
            "learning_stats",
            _player_doc_id(actual_player),
            {
                "category": "player",
                "player_name": actual_player,
                "correct_count": increment(1),
                "actual_reveal_count": increment(1),
                "total_count": increment(1),
                "updated_at": server_timestamp(),
            },
        )


@app.post("/game/start", response_model=QuestionResponse)
async def start_game(req: GameStartRequest):
    """Initialize a new game and return the first question."""
    del req
    game_id = str(uuid.uuid4())

    try:
        learning_stats = _load_learning_stats()
    except FirestoreUnavailable as exc:
        raise _firestore_error(exc) from exc

    remaining = _rank_players_by_learning(PLAYERS.copy(), learning_stats)
    asked: List[Dict[str, Any]] = []
    top_fields = _weighted_field_splits(remaining, asked, learning_stats)
    summary = summarize_candidates(remaining, top_n=5)

    try:
        question_data = ask_next_question(summary, top_fields, asked)
    except Exception as exc:
        print(f"Gemini error: {exc}")
        question_data = _fallback_question()

    turn_count = 1
    confidence = calculate_confidence(len(remaining), TOTAL_PLAYERS, turn_count)
    asked.append(
        {
            "question": question_data.get("question"),
            "targets_field": question_data.get("targets_field"),
            "turn": turn_count,
        }
    )

    try:
        set_doc(
            "game_sessions",
            game_id,
            {
                "game_id": game_id,
                "status": "active",
                "remaining_player_ids": [_player_id(player) for player in remaining],
                "asked_questions": asked,
                "history": [],
                "turn_count": turn_count,
                "confidence": confidence,
                "last_asked_field": question_data.get("targets_field"),
                "created_at": server_timestamp(),
                "updated_at": server_timestamp(),
            },
            merge=False,
        )
        _record_turn(
            game_id,
            {
                "turn": turn_count,
                "event": "question",
                "question": question_data.get("question"),
                "targets_field": question_data.get("targets_field"),
                "remaining_count": len(remaining),
                "confidence": confidence,
            },
        )
    except FirestoreUnavailable as exc:
        raise _firestore_error(exc) from exc

    return QuestionResponse(
        game_id=game_id,
        action="question",
        question=question_data.get("question", "Is your player an all-rounder?"),
        reaction=question_data.get("reaction", "The oracle awakens..."),
        thinkingMsg=question_data.get("thinkingMsg", "Consulting IPL records..."),
        confidence=min(int(confidence * 100), 99),
        remaining_count=len(remaining),
        question_number=turn_count,
    )


@app.post("/game/answer")
async def submit_answer(req: GameAnswerRequest):
    """Process user answer and return next question or guess."""
    answer = _normalize_answer(req.answer)

    try:
        session = get_doc("game_sessions", req.game_id)
    except FirestoreUnavailable as exc:
        raise _firestore_error(exc) from exc

    if not session:
        raise HTTPException(status_code=404, detail="Game session not found")
    if session.get("status") not in {"active", "guessed"}:
        raise HTTPException(status_code=409, detail="Game session is already finished")

    remaining = _players_from_ids(session.get("remaining_player_ids", ALL_PLAYER_IDS))
    asked = session.get("asked_questions", [])
    history = session.get("history", [])
    last_field = session.get("last_asked_field")

    if last_field and answer not in {"unknown", "maybe"}:
        remaining = filter_players(remaining, last_field, answer)

    turn_count = int(session.get("turn_count", 0) or 0) + 1
    history.append({"answer": answer, "field": last_field, "turn": turn_count})
    confidence = calculate_confidence(len(remaining), TOTAL_PLAYERS, turn_count)

    try:
        learning_stats = _load_learning_stats()
    except FirestoreUnavailable as exc:
        raise _firestore_error(exc) from exc

    remaining = _rank_players_by_learning(remaining, learning_stats)
    max_questions = 10
    should_guess = confidence >= 0.80 or len(remaining) <= 1 or turn_count >= max_questions

    base_session_update = {
        "remaining_player_ids": [_player_id(player) for player in remaining],
        "history": history,
        "turn_count": turn_count,
        "confidence": confidence,
        "updated_at": server_timestamp(),
    }

    if should_guess:
        if remaining:
            guess = _build_guess(req.game_id, remaining[0], confidence)
        else:
            guess = GuessResponse(
                game_id=req.game_id,
                action="guess",
                playerName="MS Dhoni",
                playerTeam="Chennai Super Kings",
                playerEmoji="CROWN",
                confidence=55,
                guessReason="The oracle is uncertain, but I sense you're thinking of a legendary captain.",
            )

        try:
            set_doc("game_sessions", req.game_id, base_session_update)
            _save_current_guess(req.game_id, guess, remaining)
            _record_turn(
                req.game_id,
                {
                    "turn": turn_count,
                    "event": "guess",
                    "answer": answer,
                    "field": last_field,
                    "guess": guess.model_dump(),
                    "remaining_count": len(remaining),
                    "confidence": confidence,
                },
            )
        except FirestoreUnavailable as exc:
            raise _firestore_error(exc) from exc
        return guess

    top_fields = _weighted_field_splits(remaining, asked, learning_stats)
    summary = summarize_candidates(remaining, top_n=5)

    try:
        question_data = ask_next_question(summary, top_fields, asked)
    except Exception as exc:
        print(f"Gemini error: {exc}")
        question_data = {
            "question": "Is your player still playing IPL?",
            "reaction": "Interesting pattern emerging...",
            "thinkingMsg": "Analyzing responses...",
            "targets_field": "akinator_tags.is_active_2025",
        }

    asked.append(
        {
            "question": question_data.get("question"),
            "targets_field": question_data.get("targets_field"),
            "turn": turn_count,
        }
    )
    base_session_update.update(
        {
            "status": "active",
            "asked_questions": asked,
            "last_asked_field": question_data.get("targets_field"),
        }
    )

    try:
        set_doc("game_sessions", req.game_id, base_session_update)
        _record_turn(
            req.game_id,
            {
                "turn": turn_count,
                "event": "question",
                "answer": answer,
                "previous_field": last_field,
                "question": question_data.get("question"),
                "targets_field": question_data.get("targets_field"),
                "remaining_count": len(remaining),
                "confidence": confidence,
            },
        )
    except FirestoreUnavailable as exc:
        raise _firestore_error(exc) from exc

    return QuestionResponse(
        game_id=req.game_id,
        action="question",
        question=question_data.get("question", "Next question?"),
        reaction=question_data.get("reaction", "Interesting..."),
        thinkingMsg=question_data.get("thinkingMsg", "Processing..."),
        confidence=min(int(confidence * 100), 99),
        remaining_count=len(remaining),
        question_number=turn_count,
    )


@app.get("/health")
async def health():
    """Health check endpoint."""
    firestore_configured = True
    firestore_error = None
    try:
        get_firestore_client()
    except Exception as exc:
        firestore_configured = False
        firestore_error = str(exc)
    return {
        "status": "ok",
        "players_loaded": len(PLAYERS),
        "firestore_configured": firestore_configured,
        "firestore_error": firestore_error,
    }


@app.post("/game/feedback")
async def submit_feedback(req: GameFeedbackRequest):
    """Persist final feedback and update lightweight learning statistics."""
    try:
        session = get_doc("game_sessions", req.game_id)
    except FirestoreUnavailable as exc:
        raise _firestore_error(exc) from exc

    if not session:
        raise HTTPException(status_code=404, detail="Game session not found")

    current_guess = session.get("current_guess") or {}
    guessed_player = req.guessed_player or current_guess.get("playerName")
    confidence = req.confidence if req.confidence is not None else current_guess.get("confidence")

    feedback_doc = {
        "game_id": req.game_id,
        "was_correct": req.was_correct,
        "guessed_player": guessed_player,
        "actual_player": req.actual_player,
        "confidence": confidence,
        "turn_count": session.get("turn_count"),
        "history": session.get("history", []),
        "asked_questions": session.get("asked_questions", []),
        "created_at": server_timestamp(),
    }

    try:
        feedback_id = add_doc("guess_feedback", feedback_doc)
        _update_learning_stats(session, req.was_correct, guessed_player, req.actual_player)
        set_doc(
            "game_sessions",
            req.game_id,
            {
                "status": "completed",
                "feedback_id": feedback_id,
                "feedback": {
                    "was_correct": req.was_correct,
                    "guessed_player": guessed_player,
                    "actual_player": req.actual_player,
                    "confidence": confidence,
                },
                "updated_at": server_timestamp(),
            },
        )
    except FirestoreUnavailable as exc:
        raise _firestore_error(exc) from exc

    return {"status": "feedback_recorded", "feedback_id": feedback_id}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
