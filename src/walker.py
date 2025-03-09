import random
import chess
import sys

from src.api import get_move_stats
from src.logger import logger
from src.divergence import find_divergence
sys.path.append("..")  # Add parent directory to path
from parameters import MIN_PLY, MAX_PLY, MOVE_WEIGHTS, MIN_GAMES, BASE_THRESHOLD, PENALTY_PER_PLY


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
    board = chess.Board()
    fen = board.fen()
    best_divergence = None
    best_score = 0

    for ply in range(max_ply):
        moves, total = get_move_stats(fen, base_rating)
        if not moves or total < MIN_GAMES:
            return None
        
        top_moves = moves[:4]
        move_choices = [m[0] for m in top_moves]
        weights = MOVE_WEIGHTS[:len(move_choices)]
        move = random.choices(move_choices, weights=weights, k=1)[0]
        board.push_uci(move)
        fen = board.fen()

        if ply < min_ply:
            continue

        divergence = find_divergence(fen, base_rating, target_rating)
        if divergence:
            gap = divergence["target_freqs"][0] - divergence["base_freqs"][0]
            win_rate_diff = 0  # Placeholder; add if API supports
            threshold = BASE_THRESHOLD - (ply - min_ply) * PENALTY_PER_PLY
            score = gap + win_rate_diff
            if score > best_score and gap >= threshold:
                best_score = score
                best_divergence = divergence
                best_divergence["ply"] = ply + 1

    return best_divergence

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