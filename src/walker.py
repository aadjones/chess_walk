from parameters import DIVERGENCE_THRESHOLD, MAX_PLY, MIN_GAMES, MIN_PLY, STARTING_FEN, TEMPERATURE
import random
import sys
import os
import pandas as pd
import chess

from src.api import get_move_stats
from src.divergence import find_divergence
from src.logger import logger

# Add parent directory to path
sys.path.append("..")

def choose_weighted_move(fen, base_rating, temperature=TEMPERATURE):
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
    
    logger.debug(f"Moves: {[(m['uci'], m['freq']) for m in moves]}, Scaled Weights: {normalized_weights}, Selected move: {chosen_move}")
    return chosen_move

def evaluate_divergence(fen, base_rating, target_rating, ply):
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
        logger.debug(f"Snapshot at ply {ply}: divergence found with top_base_move={divergence['top_base_move']}, top_target_move={divergence['top_target_move']}")
        return divergence
    else:
        logger.info(f"Snapshot at ply {ply}: no divergence found")
        return None

def validate_initial_position(fen, base_rating, target_rating):
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

def create_puzzle_data(divergence, base_rating, target_rating, ply):
    """
    Creates a dictionary containing puzzle data for the given divergence.

    Args:
        divergence (dict): Divergence data containing base_df, target_df, and fen.
        base_rating (str): Rating band for base cohort.
        target_rating (str): Rating band for target cohort.
        ply (int): Current ply number.

    Returns:
        dict: Puzzle data dictionary.
    """
    return {
        "fen": divergence["fen"],
        "base_rating": base_rating,
        "target_rating": target_rating,
        "ply": ply,
        "base_top_moves": divergence["base_df"]["Move"].tolist(),
        "base_freqs": divergence["base_df"]["Freq"].tolist(),
        "base_wdls": list(zip(
            divergence["base_df"]["White %"] / 100,
            divergence["base_df"]["Draw %"] / 100,
            divergence["base_df"]["Black %"] / 100
        )),
        "target_top_moves": divergence["target_df"]["Move"].tolist(),
        "target_freqs": divergence["target_df"]["Freq"].tolist(),
        "target_wdls": list(zip(
            divergence["target_df"]["White %"] / 100,
            divergence["target_df"]["Draw %"] / 100,
            divergence["target_df"]["Black %"] / 100
        )),
    }

def build_puzzle_dataframe(divergence, fen, base_rating, target_rating, puzzle_idx, ply):
    """
    Builds a DataFrame for the puzzle with base and target cohort data.

    Args:
        divergence (dict): Divergence data containing base_df and target_df.
        fen (str): The FEN of the position.
        base_rating (str): Rating band for base cohort.
        target_rating (str): Rating band for target cohort.
        puzzle_idx (int): Index of the puzzle.
        ply (int): Current ply number.

    Returns:
        pd.DataFrame: Combined DataFrame with base and target cohort data, indexed by Cohort, Row, and PuzzleIdx.
    """
    base_df = divergence["base_df"].assign(
        FEN=fen,
        Rating=base_rating,
        PuzzleIdx=puzzle_idx,
        Ply=ply,
    )
    target_df = divergence["target_df"].assign(
        FEN=fen,
        Rating=target_rating,
        PuzzleIdx=puzzle_idx,
        Ply=ply,
    )
    puzzle_df = pd.concat([base_df, target_df], keys=["base", "target"])
    puzzle_df = puzzle_df.set_index("PuzzleIdx", append=True)
    puzzle_df.index = puzzle_df.index.set_names(["Cohort", "Row", "PuzzleIdx"])
    return puzzle_df

def save_puzzle_to_csv(puzzle_df, output_path="output/puzzles.csv"):
    """
    Saves the puzzle DataFrame to a CSV file, appending to existing data if it exists.

    Args:
        puzzle_df (pd.DataFrame): DataFrame containing puzzle data.
        output_path (str): Path to the output CSV file.
    """
    if os.path.exists(output_path):
        try:
            existing_df = pd.read_csv(output_path, index_col=[0, 1, 2])
            max_existing_idx = existing_df.index.get_level_values("PuzzleIdx").max() if not existing_df.empty else -1
            logger.debug(f"Max existing PuzzleIdx: {max_existing_idx}")
            # Adjust puzzle_idx to continue from the highest existing index
            puzzle_idx = max_existing_idx + 1
            puzzle_df = puzzle_df.reset_index(level="PuzzleIdx")
            puzzle_df["PuzzleIdx"] = puzzle_idx
            puzzle_df = puzzle_df.set_index("PuzzleIdx", append=True)
            puzzle_df.index = puzzle_df.index.set_names(["Cohort", "Row", "PuzzleIdx"])
            puzzle_df = pd.concat([existing_df, puzzle_df])
        except Exception as e:
            logger.warning(f"Error loading existing puzzles.csv: {e}. Overwriting.")
            puzzle_idx = 0
            puzzle_df = puzzle_df.reset_index(level="PuzzleIdx")
            puzzle_df["PuzzleIdx"] = puzzle_idx
            puzzle_df = puzzle_df.set_index("PuzzleIdx", append=True)
            puzzle_df.index = puzzle_df.index.set_names(["Cohort", "Row", "PuzzleIdx"])
    puzzle_df.to_csv(output_path)
    logger.debug(f"After saving, puzzles.csv has {len(puzzle_df.index.get_level_values('PuzzleIdx').unique())} unique PuzzleIdx values.")

def generate_and_save_puzzles(base_rating, target_rating, min_ply=MIN_PLY, max_ply=MAX_PLY):
    """
    Generates puzzles by performing a random walk and saving positions with significant divergence.

    Args:
        base_rating (str): Rating band for base cohort.
        target_rating (str): Rating band for target cohort.
        min_ply (int): Minimum ply to start checking for divergence.
        max_ply (int): Maximum ply for the random walk.

    Returns:
        list: List of puzzle data dictionaries.
    """
    logger.info(
        f"Starting random walk with divergence: base_rating={base_rating}, "
        f"target_rating={target_rating}, min_ply={min_ply}, max_ply={max_ply}"
    )
    board = chess.Board(STARTING_FEN)
    fen = board.fen()
    added_puzzles = []
    logger.debug(f"Initial position: {fen}")

    # Validate initial position
    if not validate_initial_position(fen, base_rating, target_rating):
        return added_puzzles

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
                logger.warning(f"Aborting walk at ply {ply+1} due to missing move data for target rating {target_rating}")
                break
            logger.info(f"Snapshot at ply {ply+1}: no divergence found")
            continue

        # Save every divergence detected (no gap threshold!)
        logger.info(f"Significant divergence found at ply {ply+1}")
        puzzle_data = create_puzzle_data(divergence, base_rating, target_rating, ply + 1)
        added_puzzles.append(puzzle_data)

        # Build and save the puzzle DataFrame
        puzzle_idx = len(added_puzzles) - 1
        logger.debug(f"Assigning PuzzleIdx: {puzzle_idx}")
        puzzle_df = build_puzzle_dataframe(divergence, fen, base_rating, target_rating, puzzle_idx, ply + 1)
        save_puzzle_to_csv(puzzle_df)

        logger.info(f"Saved puzzle: {divergence['fen'][:20]}...")

    # Log the result of the walk
    if added_puzzles:
        logger.info(f"Random walk completed with {len(added_puzzles)} puzzles saved to CSV")
    else:
        logger.info("Random walk completed without finding any significant divergence")
    return added_puzzles