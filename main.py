import os
from dotenv import load_dotenv
from parameters import BASE_RATING, TARGET_RATING
from src.walker import random_walk
from src.divergence import find_divergence
from src.puzzle_bank import save_bank
from src.logger import logger

from parameters import STUDY_ID

load_dotenv()  # Load variables from .env file

def main(num_positions=10):
    logger.info(f"Starting puzzle generation with {num_positions} positions")
    logger.info(f"Base rating: {BASE_RATING}, Target rating: {TARGET_RATING}")
    
    puzzles = []
    for i in range(num_positions):
        logger.info(f"Generating position {i+1}/{num_positions}")
        fen = random_walk(BASE_RATING)
        if fen:
            logger.info(f"Found candidate position: {fen[:30]}...")
            puzzle = find_divergence(fen, BASE_RATING, TARGET_RATING)
            if puzzle:
                puzzles.append(puzzle)
                logger.info(f"Added puzzle: {puzzle['fen'][:20]}...")
            else:
                logger.warning(f"No divergence found for position {i+1}")
        else:
            logger.warning(f"Failed to generate position {i+1}")
    
    if puzzles:
        save_bank(puzzles)
        logger.info(f"Saved {len(puzzles)} puzzles to output/puzzles.json")
    else:
        logger.warning("No puzzles were generated")
    
if __name__ == "__main__":
    logger.info("=== Starting Chess Divergence Puzzle Generator ===")
    main()
    logger.info("=== Finished Chess Divergence Puzzle Generator ===")