import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID", "")
    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")

    GENAI_PROVIDER = os.getenv("GENAI_PROVIDER", "gemini")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./skillsprint.db")
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "20"))
    
    # Policy precedence (highest first)
    POLICY_PRECEDENCE = [
        "Latest Approved Policy",
        "Department SOP",
        "Official FAQ",
        "Informal Guidance"
    ]

settings = Settings()
