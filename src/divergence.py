from parameters import DIVERGENCE_THRESHOLD, MIN_GAMES
import sys

from src.api import get_move_stats
from src.logger import logger

sys.path.append("..")  # Add parent directory to path

def find_divergence(fen, base_rating, target_rating):
    """
    Find positions where higher-rated players prefer a different move than lower-rated players.

    Args:
        fen (str): The chess position in FEN notation
        base_rating (str): Lower rating band
        target_rating (str): Higher rating band

    Returns:
        dict: Puzzle data if divergence found, None otherwise
    """
    logger.info(f"Analyzing position for divergence between ratings {base_rating} and {target_rating}")
    logger.debug(f"Position: {fen}")

    base_moves, base_total = get_move_stats(fen, base_rating)
    target_moves, target_total = get_move_stats(fen, target_rating)

    if not base_moves or not target_moves:
        logger.warning("Missing move data for at least one rating band")
        return None

    if base_total < MIN_GAMES or target_total < MIN_GAMES:
        logger.warning(f"Insufficient games: base={base_total}, target={target_total}, min required={MIN_GAMES}")
        return None

    # Extract move data from dictionaries
    base_dict = {move["uci"]: move["freq"] for move in base_moves}  # {uci: freq}
    target_dict = {move["uci"]: move["freq"] for move in target_moves}  # {uci: freq}

    # Sort moves by frequency in descending order
    sorted_base_moves = sorted(base_moves, key=lambda x: x["freq"], reverse=True)
    sorted_target_moves = sorted(target_moves, key=lambda x: x["freq"], reverse=True)

    # Extract top moves for both ratings
    top_base_move = sorted_base_moves[0]["uci"] if sorted_base_moves else None
    top_target_move = sorted_target_moves[0]["uci"] if sorted_target_moves else None

    # Create arrays of moves and frequencies
    base_top_moves = [move["uci"] for move in sorted_base_moves]
    base_freqs = [move["freq"] for move in sorted_base_moves]
    base_wdls = [(m["win_rate"], m["draw_rate"], m["loss_rate"]) for m in base_moves]
    target_top_moves = [move["uci"] for move in sorted_target_moves]
    target_freqs = [move["freq"] for move in sorted_target_moves]
    target_wdls = [(m["win_rate"], m["draw_rate"], m["loss_rate"]) for m in target_moves]

    # Get the top move frequencies
    base_freq = base_dict.get(top_base_move, 0)
    target_freq_of_base_move = target_dict.get(top_base_move, 0)

    logger.info(f"Top base move: {top_base_move} (Base: {base_freq:.2f}, Target: {target_freq_of_base_move:.2f})")
    logger.info(f"Top target move: {top_target_move} ({target_dict.get(top_target_move, 0):.2f})")

    # First check if the top moves are different
    if top_base_move != top_target_move:
        # Calculate how much less frequently the base's top move is played in the target rating
        diff = base_freq - target_freq_of_base_move

        logger.debug(f"Move frequency difference: {diff:.2f} (threshold: {DIVERGENCE_THRESHOLD})")

        if diff >= DIVERGENCE_THRESHOLD:
            logger.info(
                f"Divergence found! Base move: {top_base_move} (Base: {base_freq:.2f}, Target: {target_freq_of_base_move:.2f})"
            )
            return {
                "fen": fen,
                "base_top_moves": base_top_moves,
                "base_freqs": base_freqs,
                "base_wdls": base_wdls,
                "target_top_moves": target_top_moves,
                "target_freqs": target_freqs,
                "target_wdls": target_wdls,
            }
    else:
        logger.info("No divergence - same top move in both rating bands")

    return None