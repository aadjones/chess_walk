# config.py
"""Configuration constants for the application."""

PUZZLES_CSV_PATH = "output/puzzles.csv"

# Column Names (makes refactoring easier if these change)
COL_PUZZLE_IDX = "PuzzleIdx"
COL_COHORT_PAIR = "CohortPair"
COL_COHORT = "Cohort"
COL_FEN = "FEN"
COL_MOVE = "Move"
COL_FREQ = "Freq"
COL_GAMES = "Games"
COL_RATING = "Rating"
COL_WHITE_PERC = "White %"
COL_DRAW_PERC = "Draw %"
COL_BLACK_PERC = "Black %"

# Cohort Identifiers
BASE_COHORT_ID = "base"
TARGET_COHORT_ID = "target"

# Display column order
DISPLAY_COLS = ["Move", "Games", "W/D/L", "Freq"]