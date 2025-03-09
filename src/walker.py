import random
import chess
import sys

from src.api import get_move_stats
from src.logger import logger
from src.divergence import find_divergence
from src.puzzle_bank import add_puzzle
sys.path.append("..")  # Add parent directory to path
from parameters import MIN_PLY, MAX_PLY, MOVE_WEIGHTS, MIN_GAMES, PENALTY_PER_PLY, DIVERGENCE_THRESHOLD


def random_walk(base_rating, target_ply=None):
    """
    Performs a random walk through chess positions starting from the initial position.
    At each step, chooses one of the top moves based on weighted probabilities.
    
    Args:
        base_rating (str): Rating band to use for move selection
        target_ply (int, optional): Desired length of the walk in half-moves. If None, randomly chosen.
        
    Returns:
        str: FEN of the final position, or None if the walk could not be completed
    """
    if target_ply is None:
        target_ply = random.randint(MIN_PLY, MAX_PLY)
    
    logger.info(f"Starting random walk to depth {target_ply} plies with rating band {base_rating}")
    board = chess.Board()
    fen = board.fen()
    logger.debug(f"Initial position: {fen}")

    for ply in range(target_ply):
        logger.debug(f"Ply {ply+1}/{target_ply}")
        moves, total = get_move_stats(fen, base_rating)
        
        if not moves or total < MIN_GAMES:  # Too rare, abort
            logger.warning(f"Insufficient data at ply {ply+1}: moves={bool(moves)}, total={total}")
            return None
            
        top_moves = moves[:4]  # Top 4 moves
        logger.debug(f"Top moves: {top_moves}")
        
        move_choices = [m[0] for m in top_moves]
        weights = MOVE_WEIGHTS[:len(move_choices)]
        move = random.choices(move_choices, weights=weights, k=1)[0]
        logger.debug(f"Selected move: {move}")
        
        fen = apply_move(fen, move)
        logger.debug(f"New position: {fen}")
        
    logger.info(f"Random walk completed successfully - final position: {fen[:30]}...")
    return fen

# Updated to include divergence after each ply
def random_walk_with_divergence(base_rating, target_rating, min_ply=10, max_ply=24):
    logger.info(f"Starting random walk with divergence: base_rating={base_rating}, target_rating={target_rating}, min_ply={min_ply}, max_ply={max_ply}")
    board = chess.Board()
    fen = board.fen()
    divergence_positions = []
    logger.debug(f"Initial position: {fen}")

    for ply in range(max_ply):
        logger.debug(f"Processing ply {ply+1}/{max_ply}")
        moves, total = get_move_stats(fen, base_rating)
        if not moves or total < MIN_GAMES:
            logger.warning(f"Insufficient data at ply {ply+1}: moves={bool(moves)}, total={total}")
            return None
        
        top_moves = moves[:4]
        logger.debug(f"Top moves: {top_moves}")
        move_choices = [m[0] for m in top_moves]
        weights = MOVE_WEIGHTS[:len(move_choices)]
        move = random.choices(move_choices, weights=weights, k=1)[0]
        logger.debug(f"Selected move: {move}")
        board.push_uci(move)
        fen = board.fen()
        logger.debug(f"New position: {fen[:30]}...")

        if ply < min_ply:
            logger.debug(f"Skipping divergence check (ply {ply+1} < min_ply {min_ply})")
            continue

        logger.debug(f"Checking for divergence at ply {ply+1}")
        divergence = find_divergence(fen, base_rating, target_rating)
        if divergence:
            gap = divergence["target_freqs"][0] - divergence["base_freqs"][0]
            win_rate_diff = 0  # Placeholder; add if API supports
            score = gap + win_rate_diff
            logger.debug(f"Divergence found - gap: {gap:.4f}, threshold: {DIVERGENCE_THRESHOLD:.4f}, score: {score:.4f}")
            
            if gap >= DIVERGENCE_THRESHOLD:
                logger.info(f"Significant divergence found at ply {ply+1} with gap {gap:.4f}")
                divergence["ply"] = ply + 1
                divergence["score"] = score
                divergence_positions.append(divergence)
        else:
            logger.debug(f"No divergence found at ply {ply+1}")

    if divergence_positions:
        logger.info(f"Random walk completed with {len(divergence_positions)} significant divergence positions")
    else:
        logger.info("Random walk completed without finding any significant divergence")
    return divergence_positions

def apply_move(fen, move):
    """
    Applies a UCI move to a position given in FEN notation.
    
    Args:
        fen (str): The starting position in FEN notation
        move (str): The move in UCI notation
        
    Returns:
        str: The resulting position in FEN notation
    """
    try:
        board = chess.Board(fen)
        board.push_uci(move)
        return board.fen()
    except Exception as e:
        logger.error(f"Error applying move {move} to position {fen}: {e}")
        return fen  # Return original FEN if there was an error

def generate_and_save_puzzles(base_rating, target_rating, min_ply=10, max_ply=24):
    """
    Performs a random walk, detects divergences, and saves puzzles directly to the puzzle bank.
    
    Args:
        base_rating (str): Rating band for base players
        target_rating (str): Rating band for target players
        min_ply (int): Minimum number of plies before checking for divergence
        max_ply (int): Maximum number of plies to walk
        
    Returns:
        list: List of puzzles that were added to the bank
    """
    logger.info(f"Starting random walk with divergence: base_rating={base_rating}, target_rating={target_rating}, min_ply={min_ply}, max_ply={max_ply}")
    board = chess.Board()
    fen = board.fen()
    added_puzzles = []
    logger.debug(f"Initial position: {fen}")

    for ply in range(max_ply):
        logger.debug(f"Processing ply {ply+1}/{max_ply}")
        moves, total = get_move_stats(fen, base_rating)
        if not moves or total < MIN_GAMES:
            logger.warning(f"Insufficient data at ply {ply+1}: moves={bool(moves)}, total={total}")
            return added_puzzles
        
        top_moves = moves[:4]
        logger.debug(f"Top moves: {top_moves}")
        move_choices = [m[0] for m in top_moves]
        weights = MOVE_WEIGHTS[:len(move_choices)]
        move = random.choices(move_choices, weights=weights, k=1)[0]
        logger.debug(f"Selected move: {move}")
        board.push_uci(move)
        fen = board.fen()
        logger.debug(f"New position: {fen[:30]}...")

        if ply < min_ply:
            logger.debug(f"Skipping divergence check (ply {ply+1} < min_ply {min_ply})")
            continue

        logger.debug(f"Checking for divergence at ply {ply+1}")
        divergence = find_divergence(fen, base_rating, target_rating)
        if divergence:
            gap = divergence["target_freqs"][0] - divergence["base_freqs"][0]
            logger.debug(f"Divergence found - gap: {gap:.4f}, threshold: {DIVERGENCE_THRESHOLD:.4f}")
            
            # If gap exceeds threshold, add to puzzle bank directly
            if gap >= DIVERGENCE_THRESHOLD:
                logger.info(f"Significant divergence found at ply {ply+1} with gap {gap:.4f}")
                # Add metadata to the puzzle
                divergence['base_rating'] = base_rating
                divergence['target_rating'] = target_rating
                divergence['ply'] = ply + 1
                
                # Add puzzle to the bank
                add_puzzle(divergence)
                added_puzzles.append(divergence)
                logger.info(f"Added puzzle: {divergence['fen'][:20]}...")
        else:
            logger.debug(f"No divergence found at ply {ply+1}")

    if added_puzzles:
        logger.info(f"Random walk completed with {len(added_puzzles)} puzzles added to bank")
    else:
        logger.info("Random walk completed without finding any significant divergence")
    return added_puzzles