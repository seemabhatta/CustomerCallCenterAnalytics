import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    ENABLE_HANDOFFS = os.getenv("ENABLE_HANDOFFS", "false").lower() == "true"
    DATA_DIR = os.getenv("DATA_DIR", "./data")
    
    @classmethod
    def validate(cls):
        """Validate that required settings are present."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required. Please set it in .env file")
        return True

settings = Settings()