import asyncio
import unittest
from unittest.mock import patch

from backend import api
from backend.database import _MEMORY_DB, get_doc, set_doc


def _question_payload(field="identity.is_allrounder"):
    return {
        "question": "Is your player an all-rounder?",
        "reaction": "Interesting read",
        "thinkingMsg": "Narrowing the pool",
        "targets_field": field,
    }


class GameFlowGuessGateTests(unittest.TestCase):
    def setUp(self):
        _MEMORY_DB.clear()

    def _seed_session(
        self,
        game_id,
        remaining_count=20,
        turn_count=1,
        answered_attempts=0,
        asked_count=1,
    ):
        asked_questions = [
            {
                "question": f"Question {index + 1}?",
                "targets_field": "identity.is_allrounder",
                "turn": index + 1,
            }
            for index in range(asked_count)
        ]
        history = [
            {
                "answer": "unknown",
                "field": "identity.is_allrounder",
                "question": f"Question {index + 1}?",
                "turn": index + 1,
                "answered_before_turn": index + 2,
            }
            for index in range(answered_attempts)
        ]
        set_doc(
            "game_sessions",
            game_id,
            {
                "game_id": game_id,
                "status": "active",
                "remaining_player_ids": api.ALL_PLAYER_IDS[:remaining_count],
                "asked_questions": asked_questions,
                "history": history,
                "turn_count": turn_count,
                "confidence": 0.1,
                "last_asked_field": "identity.is_allrounder",
            },
            merge=False,
        )

    def _answer(self, game_id):
        req = api.GameAnswerRequest(game_id=game_id, answer="unknown")
        return asyncio.run(api.submit_answer(req))

    def test_keeps_asking_when_confidence_is_exactly_85_and_attempts_remain(self):
        game_id = "exact-threshold"
        self._seed_session(
            game_id,
            remaining_count=20,
            turn_count=8,
            answered_attempts=7,
            asked_count=8,
        )

        with patch.object(api, "calculate_confidence", return_value=0.85), patch.object(
            api, "_load_learning_stats", return_value={}
        ), patch.object(api, "ask_next_question", return_value=_question_payload()):
            response = self._answer(game_id)

        self.assertEqual(response.action, "question")
        self.assertEqual(get_doc("game_sessions", game_id)["status"], "active")

    def test_keeps_asking_when_confidence_is_greater_than_85_before_minimum_answers(self):
        game_id = "above-threshold-too-soon"
        self._seed_session(game_id)

        with patch.object(api, "calculate_confidence", return_value=0.86), patch.object(
            api, "_load_learning_stats", return_value={}
        ), patch.object(api, "ask_next_question", return_value=_question_payload()):
            response = self._answer(game_id)

        self.assertEqual(response.action, "question")
        self.assertEqual(get_doc("game_sessions", game_id)["status"], "active")

    def test_guesses_when_confidence_is_greater_than_85_after_minimum_answers(self):
        game_id = "above-threshold-after-eight"
        self._seed_session(
            game_id,
            remaining_count=20,
            turn_count=8,
            answered_attempts=7,
            asked_count=8,
        )

        with patch.object(api, "calculate_confidence", return_value=0.86), patch.object(
            api, "_load_learning_stats", return_value={}
        ):
            response = self._answer(game_id)

        self.assertEqual(response.action, "guess")
        self.assertEqual(get_doc("game_sessions", game_id)["status"], "guessed")

    def test_keeps_asking_after_eighth_answer_when_confidence_is_low(self):
        game_id = "attempt-budget"
        self._seed_session(
            game_id,
            remaining_count=30,
            turn_count=8,
            answered_attempts=7,
            asked_count=8,
        )

        with patch.object(api, "calculate_confidence", return_value=0.25), patch.object(
            api, "_load_learning_stats", return_value={}
        ), patch.object(api, "ask_next_question", return_value=_question_payload()):
            response = self._answer(game_id)

        self.assertEqual(response.action, "question")
        self.assertEqual(get_doc("game_sessions", game_id)["status"], "active")

    def test_answer_endpoint_rejects_already_guessed_sessions(self):
        game_id = "locked-after-guess"
        self._seed_session(game_id)
        set_doc("game_sessions", game_id, {"status": "guessed"})

        with self.assertRaises(Exception) as raised:
            self._answer(game_id)

        self.assertEqual(getattr(raised.exception, "status_code", None), 409)


if __name__ == "__main__":
    unittest.main()
