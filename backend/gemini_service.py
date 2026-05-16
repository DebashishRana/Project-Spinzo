from google import genai
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load local environment variables from backend/.env
dotenv_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path)


def get_client():
    api_key = os.getenv("Gemini_API")
    if not api_key:
        raise RuntimeError(
            "Gemini_API is not set. Ensure backend/.env exists or set the environment variable."
        )
    return genai.Client(api_key=api_key)


def ping_gemini() -> str:
    client = get_client()
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Hello Gemini just say hi"
    )
    return response.text


def show_gemini_models() -> str:
    client = get_client()
    model_names = [m.name for m in client.models.list()]
    return json.dumps(model_names)


def respond(context: str, model: str) -> str:
    if not context:
        return "No context provided for the model to respond to."
    client = get_client()
    response = client.models.generate_content(
        model=model,
        contents=context
    )
    return response.text


def guess_player(top_candidates: list) -> str:
    client = get_client()
    candidates = json.dumps(top_candidates)
    prompt_text = (
        "You are a concise UI formatter. Given this JSON list of candidate objects:\n"
        f"{candidates}\n\n"
        "Return EXACTLY one short sentence in this format:\n"
        "The player is <short_name>. I am <confidence_pct>% sure.\n"
        "Do NOT add explanations or extra text."
    )
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt_text,
    )
    return response.text.strip()


if __name__ == "__main__":
    print(ping_gemini())
