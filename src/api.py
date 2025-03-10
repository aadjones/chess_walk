import sys
import time

import requests

from parameters import MIN_GAMES, RATE_LIMIT_DELAY
from src.logger import logger

sys.path.append("..")  # Add parent directory to path


def get_move_stats(fen, rating):
    """
    Fetches move statistics for a given FEN and rating range from the Lichess Explorer API.

    Args:
        fen (str): Position in FEN notation.
        rating (str): Rating band (e.g., "2000" or "1400-1600").

    Returns:
        tuple: (list of move dictionaries, total games) or (None, 0) if data is unavailable or invalid.
    """
    # Convert rating to Lichess API format (e.g., "1400-1600" -> "1400,1600")
    if "-" in rating:
        rating = rating.replace("-", ",")

    # Validate FEN (basic check for minimum fields)
    fen_fields = fen.split()
    if len(fen_fields) < 6:
        logger.warning(f"Invalid FEN string: {fen}")
        return None, 0

    active_color = fen_fields[1]  # Extract active color (second field)
    if active_color not in ["w", "b"]:
        logger.warning(f"Invalid active color in FEN: {fen}")
        return None, 0

    url = "https://explorer.lichess.ovh/lichess"
    params = {"fen": fen, "ratings": rating, "variant": "standard", "speeds": "blitz,rapid,classical", "topGames": 0}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()  # This will raise RequestException for HTTP errors (e.g., 404)
        data = response.json()
        moves = data.get("moves", [])
        if not moves:
            logger.warning(f"No moves data for {fen} at rating {rating}")
            return None, 0

        total_games = sum(m["white"] + m["draws"] + m["black"] for m in moves)
        if total_games < MIN_GAMES:
            logger.warning(f"Insufficient games ({total_games}) for {fen} at rating {rating}")
            return None, 0

        move_stats = []
        for move in moves:
            total = move["white"] + move["draws"] + move["black"]
            if total > 0:
                win_rate = move["white"] / total if active_color == "w" else move["black"] / total
                draw_rate = move["draws"] / total
                loss_rate = move["black"] / total if active_color == "w" else move["white"] / total
                # After we compute 'total' for each move...
                move_stats.append({
                    "uci": move["uci"],
                    "freq": total / total_games,
                    "win_rate": win_rate,
                    "draw_rate": draw_rate,
                    "loss_rate": loss_rate,
                    "games_white": move["white"],
                    "games_draws": move["draws"],
                    "games_black": move["black"],
                    "games_total": total,
                })

        if not move_stats:  # If no valid moves after processing
            logger.warning(f"No valid move stats for {fen} at rating {rating}")
            return None, 0

        sorted_moves = sorted(move_stats, key=lambda x: x["freq"], reverse=True)[:4]
        time.sleep(RATE_LIMIT_DELAY)  # Apply rate limiting
        return sorted_moves, total_games
    except (requests.RequestException, ValueError) as e:
        logger.error(f"API or JSON error for {fen} at rating {rating}: {e}")
        return None, 0
