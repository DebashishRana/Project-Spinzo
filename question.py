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

CORE JOB
--------
Given a structured summary of candidate fields (with entropy scores), remaining players, and question history,
generate ONE compelling yes/no question that:
1. Maximizes information gain (entropy or learned_entropy).
2. Is logically coherent (respects field dependencies).
3. Is engaging and avoids repetition.
4. Disambiguates among the remaining candidates effectively.

CRITICAL RULES
---------------
1. FIELD DEPENDENCY LOGIC
   - Do NOT ask about batting traits (left_handed, batting_position, known_for_big_runs, etc.)
     if the player is already ruled out as a non-batter/non-allrounder.
   - Do NOT ask about bowling traits (is_pacer, is_spinner, known_for_wickets, known_for_yorkers)
     if the player is ruled out as a non-bowler/non-allrounder.
   - Do NOT ask about captaincy traits if the player is a young/rookie (low seniority indicator).
   - Use context from asked_questions history to infer what is logically safe to ask.

2. HALLUCINATION PREVENTION
   - Review the asked_questions history and infer constraints:
     * If you've asked "Is your player a batsman?" and got "no", then avoid asking about
       batting-specific traits (left-handed, powerplay specialist, anchor batter, etc.).
     * If you've asked "Is this player Indian?" and got "yes", you can now ask about
       India-centric franchises or captaincy roles (captains tend to be Indian).
   - BEFORE choosing a field, reason through: "Given the answers so far, is this question
     logically safe to ask?"

3. VARIETY & ENGAGEMENT
   - Avoid asking the same field category twice (e.g., don't ask two different "known_for_*" questions in a row).
   - Prefer questions that reveal NEW dimensions of the player:
     * If you've been asking role-based questions (batter/bowler), try franchise/legacy questions next.
     * If you've been asking trait questions, try a biographical question (legend status, international star, etc.).
   - Choose natural, conversational phrasings over robotic ones:
     * ENGAGING: "Is this player known for hitting big sixes?"
     * BORING: "Does this player have the tag known_for_sixhitting?"
     * ENGAGING: "Has this player won an IPL title?"
     * BORING: "Is the has_won_ipl field true?"

4. CANDIDATE DISAMBIGUATION
   - If remaining_count ≤ 3, ask questions that directly distinguish top candidates.
     Example: If top candidates are [Dhoni, Pant, Samson] (all wicketkeepers), ask
     "Is your player a captain?" rather than another wicketkeeper question.
   - Look at the candidate summaries and identify what makes them different:
     * Different roles? Ask about a shared role they disagree on.
     * Different franchises? Ask about franchise loyalty.
     * Different eras? Ask about active vs retired status.

5. QUESTION SEQUENCING STRATEGY
   - Turn 1–2: Ask broad category questions (role, nationality).
   - Turn 3–4: Ask trait-based questions (legacy, achievement-based tags).
   - Turn 5+: Ask disambiguation questions specific to remaining candidates.
   - Avoid: Same field category two turns in a row.

6. JSON OUTPUT FORMAT (EXACT, NO MARKDOWN)
   Return ONLY a single JSON object with these keys:
   {
     "question": "<short natural yes/no question>",
     "targets_field": "<canonical field path>",
     "yes_eliminates": <int>,
     "no_eliminates": <int>,
     "confidence": <0.0–1.0>,
     "reasoning": "<brief one-line reason why this question now>",
     "reaction": "<short UI reaction phrase>",
     "thinkingMsg": "<short thinking message>"
   }
   - Do NOT wrap in markdown fences or add commentary.
   - Keep "question" concise (<15 words preferred).
   - Use "reasoning" to justify why this field avoids hallucination and is interesting now.

FIELD DOMAIN KNOWLEDGE
-----------------------
Organize fields by logical groups for variety:

  ROLE TRAITS: identity.playing_role, identity.is_wicketkeeper, identity.is_allrounder,
               identity.is_spinner, identity.is_pacer, identity.is_lefthanded

  ACHIEVEMENTS: akinator_tags.is_legend, akinator_tags.known_for_big_runs,
                akinator_tags.known_for_wickets, akinator_tags.known_for_sixhitting,
                akinator_tags.known_for_yorkers, akinator_tags.has_won_ipl

  FRANCHISE & LEGACY: akinator_tags.franchise_icon, akinator_tags.is_loyal_to_one_franchise,
                      ipl_career.is_captain, akinator_tags.is_captaincy_hub

  PLAYSTYLE: akinator_tags.is_chase_master, akinator_tags.is_anchor_batter,
             akinator_tags.is_aggressive_player, akinator_tags.is_calm_player,
             akinator_tags.is_powerplay_specialist, akinator_tags.is_death_overs_specialist,
             akinator_tags.is_clutch_player

  PROFILE: personal_info.is_indian, akinator_tags.is_active_2025, akinator_tags.international_star,
           akinator_tags.is_crowd_favorite

EXAMPLE REASONING TRACE
------------------------
Scenario: Turn 3, user has said "Yes" to "Is your player Indian?" and "No" to "Is your player a fast bowler?"

Good reasoning:
  "User is Indian and not a fast bowler, so likely a batter or spinner.
   I've asked role questions twice; next I should ask about achievement or franchise angle.
   Checking candidates: all are Indian, so I'll ask about captaincy (differentiator for Dhoni/Rohit).
   This avoids repeating role questions and disambiguates well."

Bad reasoning (AVOID):
  "The highest entropy field is is_lefthanded, so I'll ask that."
  → Problem: is_lefthanded only applies to batters. User said "not a fast bowler" but could still be
    a spinner or keeper. This is a hallucination.

ENGAGING QUESTION EXAMPLES (vs. Boring)
---------------------------------------
BORING (avoid):
  - "Is this player in the ipl_career.is_captain field set to true?"
  - "Does the player have the tag is_legend?"
  - "Is the field identity.is_allrounder true?"

ENGAGING (prefer):
  - "Is your player a captain?"
  - "Is this player considered an IPL legend?"
  - "Does your player excel at multiple skills (all-rounder)?"

  For distinguishing candidates:
  - "Is this player known for chasing down big totals?"
  - "Has your player won an IPL title with a specific franchise?"
  - "Is your player still actively playing in IPL 2025?"

FALLBACK / SAFETY
------------------
If you cannot confidently produce a non-hallucinating, engaging question, return:
{
  "question": "Is your player an all-rounder?",
  "targets_field": "identity.is_allrounder",
  "yes_eliminates": 0,
  "no_eliminates": 0,
  "confidence": 0.2,
  "reasoning": "Fallback safe question when logic is uncertain.",
  "reaction": "Hmm...",
  "thinkingMsg": "Regrouping..."
}

CONSTRAINTS YOU MUST FOLLOW
-----------------------------
1. NEVER ask the same targets_field twice in a row (check asked_questions history).
2. NEVER ask a field that contradicts known answers (e.g., left-handed if non-batter).
3. ALWAYS provide reasoning in the JSON to justify the choice.
4. ALWAYS keep the question conversational and under 15 words.
5. If remaining_count ≤ 3, use candidate names or unique traits in the question.
6. Vary field categories across turns (don't ask 3 role questions in a row).

INPUT STRUCTURE
----------------
You will receive:
{
  "fields": [
    {
      "field": "identity.is_wicketkeeper",
      "yes_count": 40,
      "no_count": 121,
      "entropy": 0.87,
      "learned_entropy": 0.75
    },
    ...
  ],
  "candidates": [
    {
      "short_name": "MS Dhoni",
      "role": "wk",
      "is_indian": true,
      "is_captain": true,
      "probability": 0.10
    },
    ...
  ],
  "asked_questions": [
    {
      "targets_field": "personal_info.is_indian",
      "answer": "yes"
    },
    ...
  ],
  "remaining_count": 161,
  "total_count": 161,
  "turn": 1
}

REASONING ALGORITHM (Internal, for you)
-----------------------------------------
1. Extract constraints from asked_questions: what do we know about the player?
2. For each candidate field in ranked order (by learned_entropy):
   a. Check: Is this field logically safe given constraints? If not, skip.
   b. Check: Is this field a new category (different from last 2 asked)? Prefer yes.
   c. Compute: yes_eliminates = total - yes_count, no_eliminates = yes_count.
   d. Score: Prefer high entropy AND high disambiguating power AND high engagement.
3. Select the top-scoring field that passes safety checks.
4. Compose a natural, engaging question targeting that field.
5. Return the JSON with reasoning.

END OF PROMPT
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

    with path.open("r", encoding="utf-8") as f: #loading the data as a json
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
    remaining_count = 0
    if field_splits:
        remaining_count = int(field_splits[0].get("yes_count", 0) or 0) + int(field_splits[0].get("no_count", 0) or 0)
    elif top_candidates_summary:
        remaining_count = len(top_candidates_summary)

    turn = len(asked_questions) + 1
    prompt = f"""
{SYSTEM_PROMPT}

GAME STATE:
{json.dumps({"remaining_count": remaining_count, "turn": turn}, indent=2)}

BEST CANDIDATE FIELDS (Ranked by Entropy):
{json.dumps(field_splits, indent=2)}

TOP 5 REMAINING PLAYERS (Summary):
{json.dumps(top_candidates_summary, indent=2)}

QUESTION HISTORY (answers are included when known):
{json.dumps(asked_questions, indent=2)}

Choose targets_field from BEST CANDIDATE FIELDS only. Use the answered history to avoid
contradicting the user's yes/no answers. Use the richer candidate context only to phrase
the question naturally and explain why this field is useful now.
"""
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
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

def _first_items(value, limit=5):
    if not isinstance(value, list):
        return []
    return [item for item in value[:limit] if item]

def _true_tag_names(tags: dict, limit=12):
    if not isinstance(tags, dict):
        return []
    return [key for key, value in tags.items() if value is True][:limit]

def summarize_candidates(remaining_players, top_n=5):
    summary = []
    prob = round(1.0 / len(remaining_players), 3) if remaining_players else 0
    for p in remaining_players[:top_n]:
        confusion = p.get("confusion_cluster") or {}
        strategy = p.get("strategic_question_planning") or {}
        summary.append({
            "short_name": p.get("short_name"),
            "full_name": p.get("full_name"),
            "nationality": get_nested_value(p, "personal_info.nationality"),
            "role": get_nested_value(p, "identity.playing_role"),
            "role_cluster": get_nested_value(p, "identity.primary_role_cluster"),
            "bat_style": get_nested_value(p, "identity.bat_style"),
            "bowl_style": get_nested_value(p, "identity.bowl_style"),
            "is_indian": get_nested_value(p, "personal_info.is_indian"),
            "is_captain": get_nested_value(p, "ipl_career.is_captain"),
            "is_wicketkeeper": get_nested_value(p, "identity.is_wicketkeeper"),
            "is_allrounder": get_nested_value(p, "identity.is_allrounder"),
            "is_spinner": get_nested_value(p, "identity.is_spinner"),
            "is_pacer": get_nested_value(p, "identity.is_pacer"),
            "is_lefthanded": get_nested_value(p, "identity.is_lefthanded"),
            "current_team": get_nested_value(p, "ipl_career.current_team"),
            "teams_played_for": _first_items(get_nested_value(p, "ipl_career.teams_played_for"), 6),
            "true_tags": _true_tag_names(p.get("akinator_tags") or {}),
            "archetypes": _first_items(p.get("player_archetypes"), 4),
            "storylines": _first_items(p.get("storylines"), 4),
            "era": _first_items(p.get("era_classification"), 4),
            "fan_perception": _first_items(p.get("fan_perception"), 4),
            "disambiguation_questions": _first_items(confusion.get("disambiguation_questions"), 3),
            "recommended_strategy": get_nested_value(p, "meta_reasoning.recommended_reasoning_strategy"),
            "high_information_questions": _first_items(strategy.get("high_information_questions"), 3),
            "probability": prob
        })
    return summary

def main():
    total_players_list = load_players()
    remaining_players = total_players_list
    total_players_count = len(total_players_list)
    asked_questions = []
    candidate_fields = get_candidate_fields()
    min_answers_before_guess = 8
    guess_confidence_threshold = 0.85

    print("Welcome to Cricket Akinator!")
    turn = 0
    while remaining_players:
        confidence = calculate_confidence(len(remaining_players), total_players_count, turn)
        if turn >= min_answers_before_guess and confidence > guess_confidence_threshold:
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
        turn += 1

        if turn >= min_answers_before_guess and new_confidence > guess_confidence_threshold:
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
