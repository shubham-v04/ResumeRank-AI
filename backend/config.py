"""
Central configuration, loaded from a .env file in this folder.

To switch LLM providers or models, you only ever need to edit .env -
no code changes anywhere else in the app. To add a new provider (e.g.
Gemini) later: add its API key here, write a _call_<provider>()
function in llm_extractor.py, and register it in the PROVIDERS dict
there. Nothing else needs to change.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Which provider to use - "groq" today, "gemini" or others later.
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()

    # Which model to call, for whichever provider is active.
    LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")

    # API keys, one per provider. Only the one matching LLM_PROVIDER
    # actually needs to be set.
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


settings = Settings()