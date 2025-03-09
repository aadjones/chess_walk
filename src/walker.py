import random
import chess
import sys

from src.api import get_move_stats
from src.logger import logger
from src.divergence import find_divergence
from src.puzzle_bank import add_puzzle
sys.path.append("..")  # Add parent directory to path
from parameters import MIN_PLY, MAX_PLY, MOVE_WEIGHTS, MIN_GAMES, DIVERGENCE_THRESHOLD


def choose_weighted_move(fen, base_rating):
    """
    Retrieves the top moves for the given position and chooses one based on weighted probabilities.
    
    Args:
        fen (str): Position in FEN notation.
        base_rating (str): Rating band to use for move selection.
    
    Returns:
        str or None: The chosen move in UCI format, or None if insufficient data.
    """
    moves, total = get_move_stats(fen, base_rating)
    if not moves or total < MIN_GAMES:
        logger.warning(f"Insufficient data: moves={bool(moves)}, total={total}")
        return None
    top_moves = moves[:4]
    move_choices = [m[0] for m in top_moves]
    weights = MOVE_WEIGHTS[:len(move_choices)]
    chosen_move = random.choices(move_choices, weights=weights, k=1)[0]
    logger.debug(f"Top moves: {top_moves}, Selected move: {chosen_move}")
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
        tuple: (divergence dictionary, gap) if divergence data is available, else (None, None)
    """
    logger.debug(f"Evaluating divergence at ply {ply}")
    divergence = find_divergence(fen, base_rating, target_rating)
    if divergence:
        gap = divergence["target_freqs"][0] - divergence["base_freqs"][0]
        logger.debug(f"Snapshot at ply {ply}: gap = {gap:.4f}, threshold = {DIVERGENCE_THRESHOLD:.4f}")
        return divergence, gap
    else:
        logger.info(f"Snapshot at ply {ply}: no divergence found")
        return None, None


def generate_and_save_puzzles(base_rating, target_rating, min_ply=MIN_PLY, max_ply=MAX_PLY):
    """
    Performs a random walk from the initial chess position, evaluates divergence at each snapshot,
    and saves puzzles to the puzzle bank if significant divergence is found.
    
    Args:
        base_rating (str): Rating band for base move selection.
        target_rating (str): Rating band for target divergence evaluation.
        min_ply (int): Minimum plies before starting divergence checks.
        max_ply (int): Maximum plies to walk.
        
    Returns:
        list: List of puzzles that were added to the bank.
    """
    logger.info(f"Starting random walk with divergence: base_rating={base_rating}, "
                f"target_rating={target_rating}, min_ply={min_ply}, max_ply={max_ply}")
    board = chess.Board()
    fen = board.fen()
    added_puzzles = []
    logger.debug(f"Initial position: {fen}")

    for ply in range(max_ply):
        logger.debug(f"Processing ply {ply+1}/{max_ply}")
        move = choose_weighted_move(fen, base_rating)
        if not move:
            logger.warning(f"Aborting walk at ply {ply+1} due to insufficient data.")
            return added_puzzles

        board.push_uci(move)
        fen = board.fen()
        logger.debug(f"New position at ply {ply+1}: {fen[:30]}...")

        if ply < min_ply:
            logger.debug(f"Skipping divergence check (ply {ply+1} < min_ply {min_ply})")
            continue

        divergence, gap = evaluate_divergence(fen, base_rating, target_rating, ply+1)
        if divergence and gap >= DIVERGENCE_THRESHOLD:
            logger.info(f"Significant divergence found at ply {ply+1} with gap {gap:.4f}")
            divergence['base_rating'] = base_rating
            divergence['target_rating'] = target_rating
            divergence['ply'] = ply + 1
            add_puzzle(divergence)
            added_puzzles.append(divergence)
            logger.info(f"Added puzzle: {divergence['fen'][:20]}...")
        elif divergence:
            logger.info(f"Snapshot at ply {ply+1} evaluated: divergence gap {gap:.4f} did not meet threshold")

    if added_puzzles:
        logger.info(f"Random walk completed with {len(added_puzzles)} puzzles added to bank")
    else:
        logger.info("Random walk completed without finding any significant divergence")
    return added_puzzles
