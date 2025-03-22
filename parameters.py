# Rating bands
# Valid rating values for the API (from documentation)
# Each value represents a range (e.g., 1400 means 1400-1599, 1600 means 1600-1799, etc.).
VALID_RATINGS = ["0", "1000", "1200", "1400", "1600", "1800", "2000", "2200", "2500"]

BASE_RATING = "2000"
TARGET_RATING = "2500"
# Ply range
MIN_PLY = 4
MAX_PLY = 20

# Starting FEN
# Configure this to start from different possible positions
STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

# Temperature for move selection
# If temperature > 1, the distribution flattens (more randomness)
# If temperature < 1, the distribution sharpens (more deterministic)
TEMPERATURE = 1.0

# Minimum number of games to consider a move
MIN_GAMES = 2

# Minimum win rate difference to consider a divergence
MIN_WIN_RATE_DELTA = 0.07

# API settings
API_BASE = "https://explorer.lichess.ovh/lichess"
RATE_LIMIT_DELAY = 1.0  # Seconds between calls
