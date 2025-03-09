# Rating bands

# According to the documentation, the ratings parameter accepts values from this enum: 
# 0, 1000, 1200, 1400, 1600, 1800, 2000, 2200, 2500. 
# Each value represents a range (e.g., 1400 means 1400-1599, 1600 means 1600-1799, etc.).

# Using comma-separated values instead of ranges
BASE_RATING = "1400" # represents 1400-1599
TARGET_RATING = "1800" # represents 1800-1999
RATING_GAP = 400

# Valid rating values for the API (from documentation)
VALID_RATINGS = [0, 1000, 1200, 1400, 1600, 1800, 2000, 2200, 2500]

# Ply range
MIN_PLY = 10
MAX_PLY = 20

# Move weights (top 4 moves)
MOVE_WEIGHTS = [0.5, 0.3, 0.15, 0.05]  # Sum to 1.0, bias toward top moves

# Divergence threshold
MIN_GAMES = 0  # Per rating band
DIVERGENCE_THRESHOLD = 0.05  # 5%+ difference in move frequency

# Add penalty settings
BASE_THRESHOLD = 0.6  # 60% at min ply
PENALTY_PER_PLY = 0.02  # Decrease threshold by 2% per ply

# API settings
API_BASE = "https://explorer.lichess.ovh/lichess"
RATE_LIMIT_DELAY = 1.0  # Seconds between calls

# Lichess study ID
STUDY_ID = "9EZJf2B0"