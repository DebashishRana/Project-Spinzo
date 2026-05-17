import math
from collections import defaultdict
from typing import List, Dict, Any, Tuple
import os

class DeductionEngine:
    def __init__(self, players_data: List[Dict[str, Any]]):
        self.players = players_data

        self.probabilities = {p["id"]: 1.0 / len(self.players) for p in self.players}
        self.asked_features = set()


        self.available_features = [
            "country", "overseas", "role", "captain", "finisher",
            "teams", "active", "batting_position", "orange_cap", "purple_cap"
        ]

    def _calculate_entropy(self, probabilities: Dict[str, float]) -> float:
        """Calculate Shannon entropy for the current state."""
        entropy = 0.0
        for p in probabilities.values():
            if p > 0:
                entropy -= p * math.log2(p)   # the formula for entropy is -summation(log(1/p)
        return entropy

    def get_best_feature(self) -> str:
        """
        Select the feature that provides the maximum information gain (reduces entropy the most).
        """
        best_feature = None
        min_expected_entropy = float("inf")

        for feature in self.available_features:
            if feature in self.asked_features:
                continue

            # Count the distribution of this feature based on current probabilities
            # This is a simplification; a full calculation considers all possible user answers.
            val_probs = defaultdict(float)
            for player in self.players:
                val = player.get(feature)
                if isinstance(val, list):
                    for v in val:
                        val_probs[f"{feature}:{v}"] += self.probabilities[player["id"]]
                else:
                    val_probs[f"{feature}:{val}"] += self.probabilities[player["id"]]

            expected_entropy = 0
            for weight in val_probs.values():
                if weight > 0:
                    expected_entropy -= weight * math.log2(weight)

            # We want MAXIMUM expected entropy (most balanced split) for the feature distribution itself
            # Inverting the logic purely for scoring (higher is better)
            score = expected_entropy
            if score < min_expected_entropy:
                min_expected_entropy = score
                best_feature = feature

        # Fallback to first available if all are scored 0
        if best_feature is None and self.available_features:
            for f in self.available_features:
                if f not in self.asked_features:
                    return f

        return best_feature

    def update_probabilities(self, feature: str, target_value: Any, answer: str):
        """
        Update player probabilities based on the answer.
        answer can be "YES", "NO", "MAYBE", "DONT_KNOW"
        """
        self.asked_features.add(feature)

        # Answer multipliers
        multiplier_map = {
            "YES": (2.0, 0.1),    # (Match multiplier, Mismatch multiplier)
            "NO": (0.1, 2.0),
            "MAYBE": (1.2, 0.8),
            "DONT_KNOW": (1.0, 1.0)
        }
        match_mult, mismatch_mult = multiplier_map.get(answer.upper(), (1.0, 1.0))

        total_prob = 0.0
        for player in self.players:
            val = player.get(feature)
            # Check if target_value is in list (e.g. teams) or matches exactly
            is_match = False
            if isinstance(val, list):
                is_match = target_value in val if target_value else True # Simplification
            else:
                is_match = (val == target_value) if target_value is not None else bool(val)

            if is_match:
                self.probabilities[player["id"]] *= match_mult
            else:
                self.probabilities[player["id"]] *= mismatch_mult

            total_prob += self.probabilities[player["id"]]

        # Normalize probabilities
        if total_prob > 0:
            for pid in self.probabilities:
                self.probabilities[pid] /= total_prob

    def get_top_candidates(self, count=3) -> List[Tuple[Dict, float]]:
        """Return the top players based on current probabilities."""
        sorted_probs = sorted(self.probabilities.items(), key=lambda x: x[1], reverse=True)
        top = []
        for pid, prob in sorted_probs[:count]:
            player_data = next(p for p in self.players if p["id"] == pid)
            top.append((player_data, prob))
        return top
