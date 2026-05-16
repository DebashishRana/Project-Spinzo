from google import genai
import json
import math
import os
import re
import sys
from pathlib import Path
from dotenv import load_dotenv


from backend.gemini_service import guess_player

SYSTEM_PROMPT = """
You are the question engine for an IPL Cricket Akinator game.

Your job: Given a structured summary of the best candidate fields (with calculated entropy)
and a small sample of the remaining players, generate the SINGLE BEST next yes/no question.

Rules:
- Choose the field from `BEST_CANDIDATE_FIELDS` with the highest entropy/information gain.
- Phrase the question in natural cricket fan language ("Does this player...?") targeting that exact field.
- Questions must be answerable Yes / No / Maybe / I don't know
- When ≤3 candidates remain, use identifying traits to distinguish them.

Return EXACTLY valid JSON only.
Do not wrap the JSON in markdown fences or add any commentary before or after the object.
The output must be a single JSON object with the fields shown in the example.

{
  "question": "Is this player a captain?",
  "targets_field": "ipl_career.is_captain",
  "yes_eliminates": 42,
  "no_eliminates": 89,
  "confidence": 0.52
}
"""

dotenv_path = Path(__file__).resolve().parent / "backend" / ".env"
load_dotenv(dotenv_path)

def get_client():
    api_key = os.getenv("Gemini_API")
    if not api_key:
        raise RuntimeError("Gemini_API environment variable is unable to fetch the api key.")
    return genai.Client(api_key=api_key)

def load_players(path=None):
    if path is None:
        path = Path(__file__).resolve().parent / "backend" / "players.json"
    else:
        path = Path(path)
        if not path.is_absolute():
            path = Path(__file__).resolve().parent / path

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict) and "players" in data:
        data = data["players"]

    if not isinstance(data, list):
        raise ValueError("players.json must contain a JSON array of player objects.")
    return data

def _extract_json(text: str) -> str:
    text = text.strip()
    fenced = re.search(r"```json\s*(\{.*?\})\s*```", text, re.S)
    if fenced:
        return fenced.group(1).strip()

    first_object = re.search(r"(\{.*\})", text, re.S)
    if first_object:
        return first_object.group(1).strip()

    return text

def ask_next_question(top_candidates_summary: list, field_splits: list, asked_questions: list) -> dict:
    client = get_client()
    prompt = f"""
{SYSTEM_PROMPT}

BEST CANDIDATE FIELDS (Ranked by Entropy):
{json.dumps(field_splits, indent=2)}

TOP 5 REMAINING PLAYERS (Summary):
{json.dumps(top_candidates_summary, indent=2)}

QUESTION HISTORY:
{json.dumps(asked_questions, indent=2)}
"""
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=prompt,
    )
    text = response.text.strip()
    json_text = _extract_json(text)
    return json.loads(json_text)

def normalize_answer(answer: str) -> str:
    answer = answer.strip().lower()
    if answer in {"yes", "y"}:
        return "yes"
    if answer in {"no", "n"}:
        return "no"
    if answer in {"maybe", "idk", "i don't know", "dont know"}:
        return "maybe"
    return ""

def ask_user_answer(question: str) -> str:
    while True:
        answer = input(f"{question}\nAnswer (yes/no/maybe): ").strip()
        normalized = normalize_answer(answer)
        if normalized:
            return normalized
        print("Please answer yes, no, or maybe.")

def get_nested_value(obj, field_path: str):
    value = obj
    for part in field_path.split("."):
        if isinstance(value, dict):
            value = value.get(part)
        else:
            return None
    return value

def filter_players(players: list, field_path: str, answer: str) -> list:
    if answer == "maybe":
        return players
    
    def matches(player):
        value = get_nested_value(player, field_path)
        if isinstance(value, bool):
            return value if answer == "yes" else not value
        if isinstance(value, list):
            return bool(value) if answer == "yes" else not bool(value)
        return bool(value) if answer == "yes" else not bool(value)
    
    return [p for p in players if matches(p)]

def calculate_confidence(remaining_count: int, total_count: int, turn: int) -> float:
    """Calculate confidence based on probability + pool elimination + turn progress."""
    if remaining_count <= 0:
        return 0.0
    if remaining_count == 1:
        return 0.99
        
    base_prob = 1.0 / remaining_count  # Chance of picking correctly randomly
    elimination_bonus = (1.0 - (remaining_count / total_count)) * 0.2  # Up to 20% bonus for eliminating most players
    turn_bonus = (turn / 8.0) * 0.1  # Up to 10% bonus as the game drags on
    
    confidence = base_prob + elimination_bonus + turn_bonus
    return min(confidence, 0.95)

def get_candidate_fields():
    return [
        "identity.playing_role",
        "identity.is_wicketkeeper",
        "identity.is_allrounder",
        "identity.is_spinner",
        "identity.is_pacer",
        "identity.is_lefthanded",
        "ipl_career.is_captain",
        "personal_info.is_indian",
        "akinator_tags.is_legend",
        "akinator_tags.is_active_2025",
        "akinator_tags.known_for_big_runs",
        "akinator_tags.known_for_wickets",
        "akinator_tags.known_for_sixhitting",
        "akinator_tags.known_for_yorkers",
        "akinator_tags.franchise_icon",
        "akinator_tags.international_star",
        "akinator_tags.has_won_ipl",
        "akinator_tags.is_chase_master",
        "akinator_tags.is_anchor_batter",
        "akinator_tags.is_aggressive_player",
        "akinator_tags.is_calm_player",
        "akinator_tags.is_powerplay_specialist",
        "akinator_tags.is_death_overs_specialist",
        "akinator_tags.is_clutch_player",
        "akinator_tags.is_crowd_favorite",
        "akinator_tags.is_loyal_to_one_franchise",
        "akinator_tags.is_captaincy_hub"
    ]

def compute_field_splits(remaining_players, candidate_fields, asked_questions):
    asked_fields = {q["targets_field"] for q in asked_questions}
    total = len(remaining_players)
    if total == 0: return []
    
    splits = []
    for field in candidate_fields:
        if field in asked_fields:
            continue
            
        yes_count = 0
        for p in remaining_players:
            val = get_nested_value(p, field)
            # Boolean or lists count as truthy if populated
            if isinstance(val, bool) and val: yes_count += 1
            elif isinstance(val, list) and val: yes_count += 1
            elif val and not isinstance(val, bool) and not isinstance(val, list): yes_count += 1 # catch other truthy strings
            
        no_count = total - yes_count
        
        if yes_count == 0 or no_count == 0:
            continue
            
        p_yes = yes_count / total
        p_no = no_count / total
        entropy = -(p_yes * math.log2(p_yes) + p_no * math.log2(p_no))
        
        splits.append({
            "field": field,
            "yes_count": yes_count,
            "no_count": no_count,
            "entropy": round(entropy, 4)
        })
        
    splits.sort(key=lambda x: x["entropy"], reverse=True)
    return splits[:5]

def summarize_candidates(remaining_players, top_n=5):
    summary = []
    prob = round(1.0 / len(remaining_players), 3) if remaining_players else 0
    for p in remaining_players[:top_n]:
        summary.append({
            "short_name": p.get("short_name"),
            "role": get_nested_value(p, "identity.playing_role"),
            "is_indian": get_nested_value(p, "personal_info.is_indian"),
            "is_captain": get_nested_value(p, "ipl_career.is_captain"),
            "probability": prob
        })
    return summary

def main():
    total_players_list = load_players()
    remaining_players = total_players_list
    total_players_count = len(total_players_list)
    asked_questions = []
    candidate_fields = get_candidate_fields()

    print("Welcome to Cricket Akinator!")
    for turn in range(8):
        confidence = calculate_confidence(len(remaining_players), total_players_count, turn)
        if len(remaining_players) <= 1 or confidence >= 0.80:
            print(f"\nConfidence reached threshold ({confidence:.0%}).")
            break

        print(f"\n--- Turn {turn + 1} ---")
        top_5_fields = compute_field_splits(remaining_players, candidate_fields, asked_questions)
        summary = summarize_candidates(remaining_players, top_n=5)
        
        try:
            question_data = ask_next_question(summary, top_5_fields, asked_questions)
        except Exception as e:
            print(f"Error getting question: {e}")
            break

        answer = ask_user_answer(question_data["question"])

        asked_questions.append({
            "question": question_data["question"],
            "targets_field": question_data["targets_field"],
            "answer": answer,
        })

        remaining_players = filter_players(
            remaining_players,
            question_data["targets_field"],
            answer,
        )
        
        new_confidence = calculate_confidence(len(remaining_players), total_players_count, turn + 1)
        print(f"{len(remaining_players)} candidates remain (Confidence: {new_confidence:.0%}).")
        
        if new_confidence >= 0.80:
            print(f"\nConfidence is high enough ({new_confidence:.0%})! Making final guess.")
            break

    if len(remaining_players) == 1:
        print("\nFinal guess:", remaining_players[0].get("short_name"))
    elif remaining_players:
        print(f"\nAI prediction from remaining {len(remaining_players)} candidates:")
        try:
            # Pass only top 10 candidates to keep the final LLM payload small
            print(guess_player(remaining_players[:10]))
        except Exception as e:
            print(f"Could not guess player: {e}")
    else:
        print("\nNo candidates remain based on answers.")

if __name__ == "__main__":
    main()