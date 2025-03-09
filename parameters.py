# Rating bands

# According to the documentation, the ratings parameter accepts values from this enum:
# 0, 1000, 1200, 1400, 1600, 1800, 2000, 2200, 2500.
# Each value represents a range (e.g., 1400 means 1400-1599, 1600 means 1600-1799, etc.).

# Using comma-separated values instead of ranges
BASE_RATING = "2000"
TARGET_RATING = "2500"
RATING_GAP = 500

# Valid rating values for the API (from documentation)
VALID_RATINGS = [0, 1000, 1200, 1400, 1600, 1800, 2000, 2200, 2500]

# Ply range
MIN_PLY = 4
MAX_PLY = 20

# Move weights (top 4 moves)
MOVE_WEIGHTS = [0.5, 0.3, 0.15, 0.05]  # Sum to 1.0, bias toward top moves

# Divergence threshold
MIN_GAMES = 0  # Per rating band
DIVERGENCE_THRESHOLD = 0.10  # 10%+ difference in move frequency

# Add penalty settings
PENALTY_PER_PLY = 0.02  # Decrease threshold by 2% per ply

# API settings
API_BASE = "https://explorer.lichess.ovh/lichess"
RATE_LIMIT_DELAY = 1.0  # Seconds between calls

# Lichess study ID
STUDY_ID = "9EZJf2B0"
