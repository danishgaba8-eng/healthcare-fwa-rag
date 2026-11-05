import os
from pathlib import Path
from dotenv import load_dotenv

env_file = Path(__file__).resolve().parent / ".env"

load_dotenv(env_file)

api_key = os.getenv("OPENAI_API_KEY")

print("API key configured:", bool(api_key))
