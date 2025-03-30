# config.py
"""
Application Configuration using Pydantic Settings Management.
Loads settings from environment variables and a .env file.
"""

import os
from pydantic import Field, field_validator, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict
import streamlit as st # Import streamlit for error display

# --- Pydantic Settings Model ---

class AppSettings(BaseSettings):
    """Defines application settings, loading from .env and environment variables."""

    # Define configuration loading behaviour
    # For pydantic-settings v2.x:
    model_config = SettingsConfigDict(
        env_file='.env',        # Load from .env file
        env_file_encoding='utf-8', # Specify encoding
        extra='ignore'          # Ignore extra fields in env/dotenv
    )
    # For pydantic-settings v1.x:
    # class Config:
    #     env_file = '.env'
    #     env_file_encoding = 'utf-8'
    #     extra = 'ignore'

    # --- Core Settings ---
    stockfish_executable: str = Field(..., validation_alias='STOCKFISH_EXECUTABLE')
    stockfish_depth: int = Field(default=15, validation_alias='STOCKFISH_DEPTH')

    # --- Derived Settings or Constants ---
    puzzles_csv_path: str = "output/puzzles.csv"

    # Column Names
    col_puzzle_idx: str = "PuzzleIdx"
    col_cohort_pair: str = "CohortPair"
    col_cohort: str = "Cohort"
    col_fen: str = "FEN"
    col_move: str = "Move" # This is UCI format initially in data
    col_freq: str = "Freq"
    col_games: str = "Games"
    col_rating: str = "Rating"
    col_white_perc: str = "White %"
    col_draw_perc: str = "Draw %"
    col_black_perc: str = "Black %"

    # Cohort Identifiers
    base_cohort_id: str = "base"
    target_cohort_id: str = "target"

    # Display column order (using SAN formatted move eventually)
    display_cols: list[str] = ["Move", "Games", "W/D/L", "Freq"]

    # --- Validation ---
    @field_validator('stockfish_executable')
    @classmethod
    def check_stockfish_path(cls, v: str) -> str:
        """Validate that the Stockfish path points to an existing file."""
        if not v:
            raise ValueError("STOCKFISH_EXECUTABLE path cannot be empty.")
        expanded_path = os.path.expanduser(os.path.expandvars(v)) # Expand ~ and $VARS
        if not os.path.exists(expanded_path):
            raise ValueError(f"Stockfish executable not found at path: {expanded_path} (Original: {v})")
        if not os.path.isfile(expanded_path):
            raise ValueError(f"Stockfish path exists, but is not a file: {expanded_path}")
        # Optionally check for execute permissions if needed (platform dependent)
        # if not os.access(expanded_path, os.X_OK):
        #     raise ValueError(f"Stockfish executable does not have execute permissions: {expanded_path}")
        return expanded_path # Return the expanded path

# --- Instantiate Settings ---
# This single instance will be imported by other modules.
# It automatically loads from .env and environment variables upon creation.
try:
    settings = AppSettings()
except ValidationError as e:
    # Display a user-friendly error in Streamlit if validation fails during startup
    st.error(
        f"❌ Configuration Error:\n"
        f"Please check your environment variables or `.env` file.\n"
        f"Details:\n{e}"
    )
    st.stop() # Stop the app if config is critical
except Exception as e:
    st.error(f"An unexpected error occurred while loading configuration: {e}")
    st.stop()