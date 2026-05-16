import json
from engine import DeductionEngine

with open("players.json", "r", encoding="utf-8") as f:
    players = json.load(f)

# Map the nested schema into the engine fields
for p in players:
    p["id"] = p.get("player_id", p.get("short_name"))
    p["country"] = p.get("personal_info", {}).get("nationality")
    p["role"] = p.get("identity", {}).get("playing_role")
    p["teams"] = p.get("ipl_career", {}).get("teams_played_for", [])
    p["captain"] = p.get("ipl_career", {}).get("is_captain")
    p["active"] = p.get("akinator_tags", {}).get("is_active_2025")
    p["batting_position"] = p.get("identity", {}).get("primary_role_cluster")
    p["orange_cap"] = False
    p["purple_cap"] = False
    p["overseas"] = not p.get("personal_info", {}).get("is_indian", True)

engine = DeductionEngine(players)

print("Best feature:", engine.get_best_feature())
print("Top candidates:")
for player, prob in engine.get_top_candidates(3):
    print(player["short_name"], prob)

# simulate one answer
engine.update_probabilities("captain", True, "YES")
print("\nAfter YES on captain:")
for player, prob in engine.get_top_candidates(3):
    print(player["short_name"], prob)