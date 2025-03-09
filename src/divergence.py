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
    
    base_dict = dict(base_moves)  # {move: frequency}
    target_dict = dict(target_moves)
    
    top_base_move = max(base_dict, key=base_dict.get)
    top_target_move = max(target_dict, key=target_dict.get)
    
    logger.info(f"Top move comparison - Base: {top_base_move} ({base_dict[top_base_move]:.2f}), Target: {top_target_move} ({target_dict[top_target_move]:.2f})")
    
    if top_base_move != top_target_move:
        base_freq = base_dict.get(top_base_move, 0)
        target_freq = target_dict.get(top_target_move, 0)
        diff = target_freq - base_freq
        
        logger.debug(f"Move frequency difference: {diff:.2f} (threshold: {DIVERGENCE_THRESHOLD})")
        
        if diff >= DIVERGENCE_THRESHOLD:
            logger.info(f"Divergence found! Base move: {top_base_move} ({base_freq:.2f}), Target move: {top_target_move} ({target_freq:.2f})")
            return {
                "fen": fen,
                "base_top_move": top_base_move,
                "base_freq": base_freq,
                "target_top_move": top_target_move,
                "target_freq": target_freq
            }
    else:
        logger.info("No divergence - same top move in both rating bands")
        
    return None