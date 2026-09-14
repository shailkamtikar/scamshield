import os

from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY was not found.")

PRIMARY_GEMINI_MODEL = os.getenv("PRIMARY_GEMINI_MODEL", "gemini-3.6-flash")
SECONDARY_GEMINI_MODEL = os.getenv("SECONDARY_GEMINI_MODEL", "gemini-3.5-flash-lite")
