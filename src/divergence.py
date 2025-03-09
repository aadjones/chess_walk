import sys

from src.api import get_move_stats
from src.logger import logger

sys.path.append("..")  # Add parent directory to path
from parameters import MIN_GAMES, DIVERGENCE_THRESHOLD


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
    
    # Convert to dictionaries
    base_dict = dict(base_moves)  # {move: frequency}
    target_dict = dict(target_moves)
    
    # Sort moves by frequency in descending order
    sorted_base_moves = sorted(base_dict.items(), key=lambda x: x[1], reverse=True)
    sorted_target_moves = sorted(target_dict.items(), key=lambda x: x[1], reverse=True)
    
    # Extract top moves for both ratings
    top_base_move = sorted_base_moves[0][0] if sorted_base_moves else None
    top_target_move = sorted_target_moves[0][0] if sorted_target_moves else None
    
    # Create arrays of moves and frequencies
    base_top_moves = [move for move, _ in sorted_base_moves]
    base_freqs = [freq for _, freq in sorted_base_moves]
    target_top_moves = [move for move, _ in sorted_target_moves]
    target_freqs = [freq for _, freq in sorted_target_moves]
    
    # Get the top move frequencies
    base_freq = base_dict.get(top_base_move, 0)
    target_freq = target_dict.get(top_target_move, 0)
    
    logger.info(f"Top move comparison - Base: {top_base_move} ({base_freq:.2f}), Target: {top_target_move} ({target_freq:.2f})")
    
    if top_base_move != top_target_move:
        diff = target_freq - base_freq
        
        logger.debug(f"Move frequency difference: {diff:.2f} (threshold: {DIVERGENCE_THRESHOLD})")
        
        if diff >= DIVERGENCE_THRESHOLD:
            logger.info(f"Divergence found! Base move: {top_base_move} ({base_freq:.2f}), Target move: {top_target_move} ({target_freq:.2f})")
            return {
                "fen": fen,
                "base_top_moves": base_top_moves,
                "base_freqs": base_freqs,
                "target_top_moves": target_top_moves,
                "target_freqs": target_freqs
            }
    else:
        logger.info("No divergence - same top move in both rating bands")
        
    return None