import os
from google import genai
import json

class LLMLayer:
    def __init__(self):
        # We explicitly use genai Client, but just for NLP mapping
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def feature_to_question(self, feature: str, value: str = None) -> str:
        """
        Convert a machine-readable feature to a natural language question.
        The LLM takes care of conversational UX.
        """
        if not self.client:
            # Fallback if no API key
            val_str = f" as {value}" if value else ""
            return f"Does your player have the attribute: {feature}{val_str}?"

        prompt = f"""
        You are an Akinator-style game host.
        Formulate a short, natural yes/no question to ask if a cricket player has the feature: '{feature}'.
        If a specific value is provided: '{value}', ask if the feature matches that value.
        Return ONLY the question string, nothing else.
        """
        try:
            response = self.client.models.generate_content(
                model="models/gemini-2.0-flash",
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            return f"Is it true that the player's {feature} matches {value}?"

    def parse_user_response(self, user_input: str) -> str:
        """
        Interpret fuzzy user input into categorical system answers.
        Returns one of: YES, NO, MAYBE, DONT_KNOW.
        """
        if not self.client:
            # basic fallback
            ui = user_input.lower()
            if "yes" in ui or "yep" in ui: return "YES"
            if "no" in ui or "nope" in ui: return "NO"
            return "DONT_KNOW"

        prompt = f"""
        Analyze the user's response: "{user_input}"
        Map this to EXACLY one of the following four categories:
        - YES
        - NO
        - MAYBE
        - DONT_KNOW
        Return ONLY the category name. No other text.
        """
        try:
            response = self.client.models.generate_content(
                model="models/gemini-2.0-flash",
                contents=prompt
            )
            text = response.text.strip().upper()
            if text in ["YES", "NO", "MAYBE", "DONT_KNOW"]:
                return text
            return "DONT_KNOW"
        except Exception:
            return "DONT_KNOW"
