import os
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI      = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE")

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
GROQ_API_KEY   = os.getenv("GROQ_API_KEY")

USE_SARVAM_LLM = os.getenv("USE_SARVAM_LLM", "false").lower() == "true"
USE_SARVAM_TTS = os.getenv("USE_SARVAM_TTS", "false").lower() == "true"