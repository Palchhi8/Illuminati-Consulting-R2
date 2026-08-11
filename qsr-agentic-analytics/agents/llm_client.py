import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def get_llm_response(system_prompt: str, user_message: str) -> str:
    provider = os.getenv("LLM_PROVIDER", "groq").strip().lower()

    if provider == "groq":
        try:
            from groq import Groq
        except ImportError as exc:
            raise ValueError("The 'groq' SDK is not installed. Install it to use LLM_PROVIDER=groq.") from exc

        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content

    if provider == "gemini":
        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise ValueError("The 'google-generativeai' SDK is not installed. Install it to use LLM_PROVIDER=gemini.") from exc

        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(
            f"{system_prompt}\n\nUser question: {user_message}",
            generation_config={"temperature": 0.2},
        )
        return response.text

    raise ValueError("Unsupported LLM_PROVIDER. Set LLM_PROVIDER to 'groq' or 'gemini'.")
