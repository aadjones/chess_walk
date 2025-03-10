import sys

import pandas as pd

from parameters import DIVERGENCE_THRESHOLD, MIN_GAMES
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
        dict: DataFrame-compatible data and metadata if divergence found, None otherwise
    """
    logger.info(f"Analyzing position for divergence between ratings {base_rating} and {target_rating}")
    logger.debug(f"Position: {fen}")

    base_moves, base_total = get_move_stats(fen, base_rating)
    target_moves, target_total = get_move_stats(fen, target_rating)

    if not base_moves or not target_moves:
        logger.warning(f"No moves data for {fen} at rating {base_rating if not base_moves else target_rating}")
        logger.warning("Missing move data for at least one rating band")
        return None

    if base_total < MIN_GAMES or target_total < MIN_GAMES:
        logger.warning(f"Insufficient games: base={base_total}, target={target_total}, min required={MIN_GAMES}")
        return None

    # Log raw move data for debugging
    logger.debug(f"Base moves (rating {base_rating}): {base_moves}")
    logger.debug(f"Target moves (rating {target_rating}): {target_moves}")
    logger.debug(f"Base total games: {base_total}, Target total games: {target_total}")

    # Prepare data for DataFrame
    base_data = [
        {
            "Move": move["uci"],
            "Games": move["games_total"],
            "White %": move["win_rate"] * 100 if move.get("active_color", "w") == "w" else move["loss_rate"] * 100,
            "Draw %": move["draw_rate"] * 100,
            "Black %": move["loss_rate"] * 100 if move.get("active_color", "w") == "w" else move["win_rate"] * 100,
            "Freq": move["freq"],  # Store the raw frequency for consistency
        }
        for move in base_moves
    ]
    target_data = [
        {
            "Move": move["uci"],
            "Games": move["games_total"],
            "White %": move["win_rate"] * 100 if move.get("active_color", "w") == "w" else move["loss_rate"] * 100,
            "Draw %": move["draw_rate"] * 100,
            "Black %": move["loss_rate"] * 100 if move.get("active_color", "w") == "w" else move["win_rate"] * 100,
            "Freq": move["freq"],  # Store the raw frequency for consistency
        }
        for move in target_moves
    ]

    base_df = pd.DataFrame(base_data)
    target_df = pd.DataFrame(target_data)

    # Log DataFrames for debugging
    logger.debug(f"Base DataFrame:\n{base_df}")
    logger.debug(f"Target DataFrame:\n{target_df}")

    # Validate using total games instead of Games sum
    if base_df["Freq"].sum() == 0 or target_df["Freq"].sum() == 0:
        logger.warning(
            f"No frequency data: base_freq_sum={base_df['Freq'].sum()}, target_freq_sum={target_df['Freq'].sum()}"
        )
        return None

    # Extract top moves for divergence check
    base_df = base_df.sort_values(by="Freq", ascending=False)
    target_df = target_df.sort_values(by="Freq", ascending=False)

    top_base_move = base_df.iloc[0]["Move"] if not base_df.empty else None
    top_target_move = target_df.iloc[0]["Move"] if not target_df.empty else None

    base_freq = base_df.iloc[0]["Freq"]
    target_freq_of_base_move = (
        target_df[target_df["Move"] == top_base_move]["Freq"].iloc[0]
        if top_base_move in target_df["Move"].values
        else 0
    )

    logger.info(f"Top base move: {top_base_move} (Base: {base_freq:.2f}, Target: {target_freq_of_base_move:.2f})")
    logger.info(f"Top target move: {top_target_move} ({target_df.iloc[0]['Freq']:.2f})")

    if top_base_move != top_target_move:
        diff = base_freq - target_freq_of_base_move
        logger.debug(f"Move frequency difference: {diff:.2f} (threshold: {DIVERGENCE_THRESHOLD})")

        if diff >= DIVERGENCE_THRESHOLD:
            logger.info(
                f"Divergence found! Base move: {top_base_move} (Base: {base_freq:.2f}, Target: {target_freq_of_base_move:.2f})"
            )
            return {
                "fen": fen,
                "base_rating": base_rating,
                "target_rating": target_rating,
                "base_df": base_df,
                "target_df": target_df,
            }
    else:
        logger.info("No divergence - same top move in both rating bands")

    return None
