# config.py
"""
Application Configuration using Pydantic Settings Management.
Loads settings from environment variables and a .env file,
with defaults suitable for Streamlit Community Cloud deployment.
"""

import os
from pydantic import Field, field_validator, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict
import streamlit as st
import shutil # To check if executable exists in PATH

# --- Default Stockfish Path for Linux/SCC ---
# Try common paths where apt might install stockfish
DEFAULT_SF_PATH_SCC = "/usr/games/stockfish"
if not os.path.exists(DEFAULT_SF_PATH_SCC):
     # Sometimes it's in /usr/bin/
     if os.path.exists("/usr/bin/stockfish"):
          DEFAULT_SF_PATH_SCC = "/usr/bin/stockfish"
     else:
          # Fallback if neither exists (will likely fail validation later if needed)
          # Or try searching PATH using shutil.which
          found_path = shutil.which("stockfish")
          if found_path:
               DEFAULT_SF_PATH_SCC = found_path
          else:
               # Keep the original default as a last resort, validation will handle it
               DEFAULT_SF_PATH_SCC = "/usr/games/stockfish"


# --- Pydantic Settings Model ---

class AppSettings(BaseSettings):
    """Defines application settings, loading from .env and environment variables."""
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

    # --- Core Settings ---
    # Use default=DEFAULT_SF_PATH_SCC for deployment
    # STOCKFISH_EXECUTABLE in .env will OVERRIDE this for local use.
    stockfish_executable: str = Field(default=DEFAULT_SF_PATH_SCC, validation_alias='STOCKFISH_EXECUTABLE')
    stockfish_depth: int = Field(default=15, validation_alias='STOCKFISH_DEPTH')

    # --- Constants ---
    positions_csv_path: str = "output/positions.csv" # Make sure this relative path is correct
    col_position_idx: str = "PositionIdx"
    col_cohort_pair: str = "CohortPair"
    col_cohort: str = "Cohort"
    col_fen: str = "FEN"
    col_move: str = "Move"
    col_freq: str = "Freq"
    col_games: str = "Games"
    col_rating: str = "Rating"
    col_white_perc: str = "White %"
    col_draw_perc: str = "Draw %"
    col_black_perc: str = "Black %"
    base_cohort_id: str = "base"
    target_cohort_id: str = "target"
    display_cols: list[str] = ["Move", "Games", "W/D/L", "Freq"]

    # --- Validation ---
    @field_validator('stockfish_executable')
    @classmethod
    def check_stockfish_path(cls, v: str) -> str:
        """Validate that the Stockfish path points to an existing file."""
        if not v:
            raise ValueError("Stockfish executable path is empty.")
        # Expand ~ and $VARS if necessary (less likely needed for SCC default path)
        expanded_path = os.path.expanduser(os.path.expandvars(v))
        if not os.path.exists(expanded_path):
            # More informative error
            raise ValueError(f"Stockfish executable not found at path: '{expanded_path}'. Check STOCKFISH_EXECUTABLE in .env (local) or packages.txt (deployment).")
        if not os.path.isfile(expanded_path):
            raise ValueError(f"Stockfish path exists, but is not a file: '{expanded_path}'")
        # Check execute permissions - crucial!
        if not os.access(expanded_path, os.X_OK):
             raise ValueError(f"Stockfish executable does not have execute permissions: '{expanded_path}'")
        return expanded_path

# --- Instantiate Settings ---
try:
    settings = AppSettings()
except ValidationError as e:
    st.error(f"❌ Configuration Error:\n{e}\nCheck .env (local) or packages.txt/default path (deployment).")
    st.stop()
except Exception as e:
    st.error(f"An unexpected error occurred while loading configuration: {e}")
    st.stop()