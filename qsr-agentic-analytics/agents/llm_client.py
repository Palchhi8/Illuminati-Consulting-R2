import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


load_dotenv(Path(__file__).resolve().parents[1] / ".env")
load_dotenv(Path(__file__).resolve().parents[2] / ".env")
logger = logging.getLogger(__name__)


def get_llm_response(system_prompt: str, user_message: str) -> str:
    provider = os.getenv("LLM_PROVIDER", "groq").strip().lower()

    if provider == "groq":
        try:
            from groq import Groq, NotFoundError
        except ImportError as exc:
            raise ValueError("The 'groq' SDK is not installed. Install it to use LLM_PROVIDER=groq.") from exc

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set. Please set GROQ_API_KEY in the environment or .env file.")

        client = Groq(api_key=api_key)
        preferred_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip()
        candidate_models = [preferred_model]
        for fallback in ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.6-27b", "llama-3.3-70b-versatile"]:
            if fallback not in candidate_models:
                candidate_models.append(fallback)

        last_error = None
        for model_name in candidate_models:
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    temperature=0.2,
                )
                content = response.choices[0].message.content
                if content:
                    return content
            except NotFoundError as err:
                logger.warning(f"Groq model '{model_name}' not found: {err}. Trying fallback...")
                last_error = err
                continue
            except Exception as err:
                logger.error(f"Groq API error with model '{model_name}': {err}")
                last_error = err
                break

        if last_error:
            raise last_error
        raise RuntimeError("Failed to obtain a response from Groq.")

    if provider == "gemini":
        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise ValueError("The 'google-generativeai' SDK is not installed. Install it to use LLM_PROVIDER=gemini.") from exc

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set. Please set GEMINI_API_KEY in the environment or .env file.")

        genai.configure(api_key=api_key)
        gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
        candidate_models = [gemini_model]
        for fallback in ["gemini-2.5-flash", "gemini-3.6-flash", "gemini-1.5-flash"]:
            if fallback not in candidate_models:
                candidate_models.append(fallback)

        last_error = None
        for model_name in candidate_models:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(
                    f"{system_prompt}\n\nUser question: {user_message}",
                    generation_config={"temperature": 0.2},
                )
                if response and response.text:
                    return response.text
            except Exception as err:
                logger.warning(f"Gemini model '{model_name}' error: {err}")
                last_error = err
                continue

        if last_error:
            raise last_error
        raise RuntimeError("Failed to obtain a response from Gemini.")

    raise ValueError("Unsupported LLM_PROVIDER. Set LLM_PROVIDER to 'groq' or 'gemini'.")
