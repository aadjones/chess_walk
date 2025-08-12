import os
import random
import sys

import chess
import pandas as pd

from parameters import MAX_PLY, MIN_GAMES, MIN_PLY, STARTING_FEN, TEMPERATURE
from src.api import get_move_stats
from src.divergence import find_divergence
from src.logger import logger

# Add parent directory to path
sys.path.append("..")


def choose_weighted_move(fen: str, base_rating: str, temperature: float = TEMPERATURE) -> str | None:
    """
    Retrieves the top moves for the given position and chooses one based on dynamically computed weights
    from the move frequencies, optionally using temperature scaling.

    Args:
        fen (str): Position in FEN notation.
        base_rating (str): Rating band to use for move selection.
        temperature (float): Temperature parameter to control randomness. Default is 1.0.

    Returns:
        str or None: The chosen move in UCI format, or None if insufficient data.
    """
    moves, total = get_move_stats(fen, base_rating)
    if not moves or total < MIN_GAMES:
        logger.warning(f"Insufficient data: moves={bool(moves)}, total={total}")
        return None

    # Use the frequency values to derive weights
    frequencies = [move["freq"] for move in moves]

    # Apply temperature scaling:
    # If temperature > 1, the distribution flattens (more randomness)
    # If temperature < 1, the distribution sharpens (more deterministic)
    scaled_weights = [f ** (1 / temperature) for f in frequencies]

    # Normalize weights so they sum to 1
    total_weight = sum(scaled_weights)
    normalized_weights = [w / total_weight for w in scaled_weights]

    move_choices = [move["uci"] for move in moves]
    chosen_move = random.choices(move_choices, weights=normalized_weights, k=1)[0]

    logger.debug(
        f"Moves: {[(m['uci'], m['freq']) for m in moves]}, Scaled Weights: {normalized_weights}, Selected move: {chosen_move}"
    )
    return chosen_move


def evaluate_divergence(fen: str, base_rating: str, target_rating: str, ply: int) -> dict | None:
    """
    Evaluates the current position for divergence between rating cohorts.

    Args:
        fen (str): The current position in FEN.
        base_rating (str): Rating band used for base move statistics.
        target_rating (str): Rating band used for target move statistics.
        ply (int): Current ply number.

    Returns:
        dict or None: Divergence dictionary if found, else None
    """
    logger.debug(f"Evaluating divergence at ply {ply}")
    divergence = find_divergence(fen, base_rating, target_rating)
    if divergence:
        logger.debug(
            f"Snapshot at ply {ply}: divergence found with top_base_move={divergence['top_base_move']}, top_target_move={divergence['top_target_move']}"
        )
        return divergence
    else:
        logger.info(f"Snapshot at ply {ply}: no divergence found")
        return None


def validate_initial_position(fen: str, base_rating: str, target_rating: str) -> bool:
    """
    Validates that the initial position has sufficient move data for both cohorts.

    Args:
        fen (str): The initial position in FEN.
        base_rating (str): Rating band for base cohort.
        target_rating (str): Rating band for target cohort.

    Returns:
        bool: True if the position has sufficient data, False otherwise.
    """
    base_moves, base_total = get_move_stats(fen, base_rating)
    target_moves, target_total = get_move_stats(fen, target_rating)
    if not base_moves or not target_moves or base_total < MIN_GAMES or target_total < MIN_GAMES:
        logger.warning(f"Insufficient initial data for FEN {fen}: base_total={base_total}, target_total={target_total}")
        return False
    return True


def create_position_data(divergence: dict, base_rating: str, target_rating: str, ply: int) -> dict:
    """
    Creates a dictionary containing position data for the given divergence.

    Args:
        divergence (dict): Divergence data containing base_df, target_df, and fen.
        base_rating (str): Rating band for base cohort.
        target_rating (str): Rating band for target cohort.
        ply (int): Current ply number.

    Returns:
        dict: Position data dictionary.
    """
    cohort_pair = f"{base_rating}-{target_rating}"
    return {
        "fen": divergence["fen"],
        "base_rating": base_rating,
        "target_rating": target_rating,
        "CohortPair": cohort_pair,
        "ply": ply,
        "base_top_moves": divergence["base_df"]["Move"].tolist(),
        "base_freqs": divergence["base_df"]["Freq"].tolist(),
        "base_wdls": list(
            zip(
                divergence["base_df"]["White %"] / 100,
                divergence["base_df"]["Draw %"] / 100,
                divergence["base_df"]["Black %"] / 100,
            )
        ),
        "target_top_moves": divergence["target_df"]["Move"].tolist(),
        "target_freqs": divergence["target_df"]["Freq"].tolist(),
        "target_wdls": list(
            zip(
                divergence["target_df"]["White %"] / 100,
                divergence["target_df"]["Draw %"] / 100,
                divergence["target_df"]["Black %"] / 100,
            )
        ),
    }


def build_position_dataframe(
    divergence: dict, fen: str, base_rating: str, target_rating: str, position_idx: int, ply: int
) -> pd.DataFrame:
    """
    Builds a DataFrame for the position with base and target cohort data.

    Args:
        divergence (dict): Divergence data containing base_df and target_df.
        fen (str): The FEN of the position.
        base_rating (str): Rating band for base cohort.
        target_rating (str): Rating band for target cohort.
        position_idx (int): Index of the position.
        ply (int): Current ply number.

    Returns:
        pd.DataFrame: Combined DataFrame with base and target cohort data, indexed by Cohort, Row, and PositionIdx.
    """
    cohort_pair = f"{base_rating}-{target_rating}"

    base_df = divergence["base_df"].assign(
        FEN=fen,
        Rating=base_rating,
        PositionIdx=position_idx,
        Ply=ply,
        CohortPair=cohort_pair,
    )
    target_df = divergence["target_df"].assign(
        FEN=fen,
        Rating=target_rating,
        PositionIdx=position_idx,
        Ply=ply,
        CohortPair=cohort_pair,
    )
    position_df = pd.concat([base_df, target_df], keys=["base", "target"])
    position_df = position_df.set_index("PositionIdx", append=True)
    position_df.index = position_df.index.set_names(["Cohort", "Row", "PositionIdx"])
    return position_df


def save_position_to_csv(position_df: pd.DataFrame, output_path: str = "output/positions.csv"):
    """
    Saves the position DataFrame to a CSV file, appending to existing data if it exists,
    and skipping rows with duplicate FENs (for the same CohortPair).

    Args:
        position_df (pd.DataFrame): DataFrame containing position data.
        output_path (str): Path to the output CSV file.
    """
    # If the incoming DataFrame already has PositionIdx in its index, reset it (dropping it)
    if "PositionIdx" in position_df.index.names:
        position_df = position_df.reset_index(level="PositionIdx", drop=True)

    if os.path.exists(output_path):
        try:
            existing_df = pd.read_csv(output_path, index_col=[0, 1, 2])
            max_existing_idx = existing_df.index.get_level_values("PositionIdx").max() if not existing_df.empty else -1
            logger.debug(f"Max existing PositionIdx: {max_existing_idx}")
            puzzle_idx = max_existing_idx + 1

            # Reset index for new data: since position_df no longer has PositionIdx as a column,
            # add it now.
            position_df["PositionIdx"] = puzzle_idx
            position_df = position_df.set_index("PositionIdx", append=True)
            position_df.index = position_df.index.set_names(["Cohort", "Row", "PositionIdx"])

            # Check for duplicate FENs within the same CohortPair
            if not existing_df.empty and "FEN" in existing_df.columns and "CohortPair" in existing_df.columns:
                duplicate_mask = position_df.apply(
                    lambda row: (
                        (existing_df["FEN"] == row["FEN"]) & (existing_df["CohortPair"] == row["CohortPair"])
                    ).any(),
                    axis=1,
                )
                if duplicate_mask.any():
                    duplicate_fens = position_df.loc[duplicate_mask, "FEN"].unique()
                    logger.info(
                        f"Skipping {len(duplicate_fens)} rows with duplicate FENs in the same cohort pair: {duplicate_fens}"
                    )
                    position_df = position_df[~duplicate_mask]
            # Concatenate new rows if any remain
            if not position_df.empty:
                position_df = pd.concat([existing_df, position_df])
            else:
                position_df = existing_df
        except Exception as e:
            logger.warning(f"Error loading existing positions.csv: {e}. Overwriting.")
            position_df = position_df.copy()
            position_df["PositionIdx"] = 0
            position_df = position_df.set_index("PositionIdx", append=True)
            position_df.index = position_df.index.set_names(["Cohort", "Row", "PositionIdx"])
    else:
        # File does not exist: assign initial PositionIdx 0.
        position_df = position_df.copy()
        position_df["PositionIdx"] = 0
        position_df = position_df.set_index("PositionIdx", append=True)
        position_df.index = position_df.index.set_names(["Cohort", "Row", "PositionIdx"])
    position_df.to_csv(output_path)
    logger.debug(
        f"After saving, positions.csv has {len(position_df.index.get_level_values('PositionIdx').unique())} unique PositionIdx values."
    )


def generate_and_save_positions(
    base_rating: str, target_rating: str, min_ply: int = MIN_PLY, max_ply: int = MAX_PLY
) -> list[dict]:
    """
    Generates positions by performing a random walk and saving positions with significant divergence.

    Args:
        base_rating (str): Rating band for base cohort.
        target_rating (str): Rating band for target cohort.
        min_ply (int): Minimum ply to start checking for divergence.
        max_ply (int): Maximum ply for the random walk.

    Returns:
        list: List of position data dictionaries.
    """
    logger.info(
        f"Starting random walk with divergence: base_rating={base_rating}, "
        f"target_rating={target_rating}, min_ply={min_ply}, max_ply={max_ply}"
    )
    board = chess.Board(STARTING_FEN)
    fen = board.fen()
    added_positions = []
    logger.debug(f"Initial position: {fen}")

    # Validate initial position
    if not validate_initial_position(fen, base_rating, target_rating):
        return added_positions

    # Perform the random walk
    for ply in range(max_ply):
        logger.debug(f"Processing ply {ply+1}/{max_ply}")
        move = choose_weighted_move(fen, base_rating)
        if not move:
            logger.warning(f"Aborting walk at ply {ply+1} due to insufficient data.")
            break

        board.push_uci(move)
        fen = board.fen()
        logger.debug(f"New position at ply {ply+1}: {fen[:30]}...")

        # Skip divergence check if before min_ply
        if ply < min_ply:
            logger.debug(f"Skipping divergence check (ply {ply+1} < min_ply {min_ply})")
            continue

        # Evaluate divergence
        divergence = evaluate_divergence(fen, base_rating, target_rating, ply + 1)
        if divergence is None:
            recent_logs = [record.getMessage() for record in logger.handlers[0].buffer[-5:]]
            logger.debug(f"Recent logs: {recent_logs}")
            if any("Missing move data" in msg for msg in recent_logs):
                logger.warning(
                    f"Aborting walk at ply {ply+1} due to missing move data for target rating {target_rating}"
                )
                break
            logger.info(f"Snapshot at ply {ply+1}: no divergence found")
            continue

        # Save every divergence detected (no gap threshold!)
        logger.info(f"Significant divergence found at ply {ply+1}")
        position_data = create_position_data(divergence, base_rating, target_rating, ply + 1)
        added_positions.append(position_data)

        # Build and save the position DataFrame
        position_idx = len(added_positions) - 1
        logger.debug(f"Assigning PositionIdx: {position_idx}")
        position_df = build_position_dataframe(divergence, fen, base_rating, target_rating, position_idx, ply + 1)
        save_position_to_csv(position_df)

        logger.info(f"Saved position: {divergence['fen'][:20]}...")

    # Log the result of the walk
    if added_positions:
        logger.info(f"Random walk completed with {len(added_positions)} positions saved to CSV")
    else:
        logger.info("Random walk completed without finding any significant divergence")
    return added_positions
