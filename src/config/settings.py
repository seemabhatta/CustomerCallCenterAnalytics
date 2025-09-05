import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application settings and configuration."""
    
    # Project paths
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    DB_DIR = DATA_DIR / "db"
    PROMPTS_DIR = DATA_DIR / "prompts"
    
    # Ensure directories exist
    DATA_DIR.mkdir(exist_ok=True)
    DB_DIR.mkdir(exist_ok=True)
    PROMPTS_DIR.mkdir(exist_ok=True)
    
    # API Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    # Default to a current, cost‑effective model
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    # Database Configuration
    TRANSCRIPTS_DB = str(DB_DIR / "transcripts.json")
    SESSIONS_DB = str(DB_DIR / "sessions.db")
    
    # Transcript Generation Configuration
    DEFAULT_CALL_DURATION_MIN = 8
    DEFAULT_CALL_DURATION_MAX = 25
    
    @classmethod
    def validate(cls):
        """Validate that required settings are present."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        return True

# Global settings instance
settings = Settings()
