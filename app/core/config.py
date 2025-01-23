from pathlib import Path
from functools import lru_cache
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
import logging
from dotenv import load_dotenv, find_dotenv

# Base directory setup
BASE_DIR = Path(__file__).resolve().parent.parent.parent
APP_DIR = Path(__file__).resolve().parent.parent

@lru_cache()
def load_env_file() -> bool:
    """Load environment variables from .env file."""
    env_file = find_dotenv(str(BASE_DIR / ".env"))
    if env_file:
        return load_dotenv(env_file)
    print(f"No .env file found in {BASE_DIR}")
    return False

# Load environment variables
load_env_file()


class BinanceSettings(BaseModel):
    """Binance configuration settings."""
    API_KEY: str = Field(
        default=os.getenv("BINANCE_API_KEY"),
        description="Binance API key"
    )
    API_SECRET: str = Field(
        default=os.getenv("BINANCE_API_SECRET"),
        description="Binance API secret"
    )

    @property
    def has_valid_config(self) -> bool:
        """Check if Binance configuration is valid."""
        return bool(self.API_KEY and self.API_SECRET)


class Settings(BaseSettings):
    """Main application settings."""
    PROJECT_NAME: str = "News Publisher"
    PROJECT_DESCRIPTION: str = "Parse news from RSS feeds and send them to Telegram groups"
    binance: BinanceSettings = Field(default_factory=BinanceSettings)
    LOGGER_NAME: str = "auto-hedge"
    LOGGER_LEVEL: str = os.getenv("LOGGING_LEVEL", "INFO")
    APP_DIR: Path = Field(default_factory=lambda: APP_DIR)
    TMP_DIR: Path = Field(default_factory=lambda: APP_DIR / "tmp")
    LOGS_DIR: Path = Field(default_factory=lambda: BASE_DIR / "logs")
    
    model_config = SettingsConfigDict(case_sensitive=True)

    @property
    def is_valid(self) -> bool:
        """Check if all required configurations are valid."""
        return all([
            self.binance.has_valid_config,
        ])

    def check_paths(self) -> bool:
        """Check if all required paths are writable."""
        try:
            test_file = self.TMP_DIR / '.write_test'
            test_file.touch()
            test_file.unlink()
            return True
        except (OSError, IOError) as e:
            logger.error(f"Path check failed: {str(e)}")
            return False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ensure_logs_dir()
        self.ensure_tmp_dir()
        if not self.check_paths():
            logger.warning("Some paths are not writable. Check permissions.")

    def ensure_tmp_dir(self):
        """Ensure temporary directory exists."""
        self.TMP_DIR.mkdir(parents=True, exist_ok=True)

    def ensure_logs_dir(self):
        """Ensure logs directory exists."""
        self.LOGS_DIR.mkdir(parents=True, exist_ok=True)

def setup_logging(settings: Settings) -> logging.Logger:
    """Configure and setup logging."""
    # Get logger instance
    logger = logging.getLogger(settings.LOGGER_NAME)
    
    # Set logger level
    logger.setLevel(settings.LOGGER_LEVEL)
    
    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname).3s | %(name)s -> %(funcName)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Prevent propagation to root logger to avoid double logging
    logger.propagate = False
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Add file handler
    log_file = settings.LOGS_DIR / "out.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

# Initialize settings
settings = Settings()

# Setup logging
logger = setup_logging(settings)

# Validate settings on import
if not settings.is_valid:
    logger.warning("Invalid configuration detected. Please check your environment variables.")