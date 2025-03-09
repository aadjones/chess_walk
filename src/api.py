from parameters import API_BASE, RATE_LIMIT_DELAY
import sys
import time
import urllib.parse

import requests

from src.logger import logger

sys.path.append("..")  # Add parent directory to path


def get_move_stats(fen, rating_band):
    """
    Fetches move statistics from the Lichess API for a given position and rating band.

    Args:
        fen (str): The chess position in FEN notation
        rating_band (str): Rating band in format "1400" or "1400,1600"

    Returns:
        tuple: (list of (move, frequency) tuples, total number of games) or (None, 0) on error
    """
    # Encode the FEN properly for URL
    encoded_fen = urllib.parse.quote(fen)

    # Format the ratings parameter according to the API requirements
    # According to docs, should be comma-separated values from: 0, 1000, 1200, 1400, 1600, 1800, 2000, 2200, 2500
    if "-" in rating_band:
        logger.warning(f"Rating band '{rating_band}' uses hyphen format instead of comma format")
        start, end = rating_band.split("-")
        valid_ratings = [0, 1000, 1200, 1400, 1600, 1800, 2000, 2200, 2500]
        try:
            start_val = int(start)
            end_val = int(end)
            # Find valid rating values within the range
            formatted_ratings = ",".join(str(r) for r in valid_ratings if start_val <= r <= end_val)
            if not formatted_ratings:
                # If no valid ratings in range, just use the closest valid rating
                closest_val = min(valid_ratings, key=lambda x: abs(x - start_val))
                formatted_ratings = str(closest_val)
            logger.info(f"Converted rating band '{rating_band}' to '{formatted_ratings}'")
        except ValueError:
            logger.error(f"Invalid rating band format: {rating_band}")
            formatted_ratings = "1400"  # Default fallback
    else:
        formatted_ratings = rating_band

    url = f"{API_BASE}?variant=standard&fen={encoded_fen}&speeds=blitz,rapid,classical&ratings={formatted_ratings}"
    logger.debug(f"API Request URL: {url}")

    try:
        logger.info(f"Fetching move stats for position: {fen[:20]}... (Rating: {formatted_ratings})")
        response = requests.get(url, headers={"Accept": "application/json"})
        logger.debug(f"API Response Status: {response.status_code}")

        if response.status_code != 200:
            logger.error(f"API error ({response.status_code}): {response.text[:100]}")
            return None, 0

        response.raise_for_status()
        data = response.json()
        logger.debug(f"API Response Data: {str(data)[:500]}...")

        if not data.get("moves"):
            logger.warning(f"No moves found for position: {fen}")
            return None, 0

        total = data.get("white", 0) + data.get("black", 0) + data.get("draws", 0)
        if total == 0:
            logger.warning(f"No games found for position: {fen}")
            return None, 0

        logger.info(f"Found {total} games and {len(data['moves'])} different moves")
        moves = [(m["uci"], (m.get("white", 0) + m.get("black", 0) + m.get("draws", 0)) / total) for m in data["moves"]]

        # Log the top moves for debugging
        for move, freq in sorted(moves, key=lambda x: x[1], reverse=True)[:3]:
            logger.debug(f"Move: {move}, Frequency: {freq:.2f}")

        time.sleep(RATE_LIMIT_DELAY)  # Respect rate limit
        return moves, total
    except requests.RequestException as e:
        logger.error(f"API request error: {e}")
        return None, 0
    except ValueError as e:
        logger.error(f"JSON parsing error: {e}")
        logger.debug(f"Response content: {response.content[:500]}")
        return None, 0
    except Exception as e:
        logger.error(f"Unexpected error processing API response: {e}")
        return None, 0
