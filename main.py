import argparse
import json

from dotenv import load_dotenv

from parameters import BASE_RATING, TARGET_RATING
from src.generate_fen_viewer import generate_fen_viewer
from src.logger import logger
from src.walker import generate_and_save_puzzles

load_dotenv()  # Load variables from .env file


def parse_args():
    parser = argparse.ArgumentParser(description="Chess Divergence Puzzle Generator")
    parser.add_argument("--num_walks", type=int, default=10, help="Number of walks to generate (default: 10)")
    return parser.parse_args()


def main(num_walks=10):
    logger.info(f"Starting puzzle generation with {num_walks} walks")
    logger.info(f"Base rating: {BASE_RATING}, Target rating: {TARGET_RATING}")

    # Track new puzzles to report count at the end
    new_puzzles_count = 0
    for i in range(num_walks):
        logger.info(f"Generating walk {i+1}/{num_walks}")
        puzzles = generate_and_save_puzzles(BASE_RATING, TARGET_RATING)
        new_puzzles_count += len(puzzles)
        if not puzzles:
            logger.warning(f"No puzzles generated for walk {i+1}")

    if new_puzzles_count > 0:
        # Read the file to get the total count for logging
        try:
            with open("output/puzzles.json", "r") as f:
                all_puzzles = json.load(f)
            logger.info(f"Added {new_puzzles_count} new puzzles (total: {len(all_puzzles)})")
        except Exception as e:
            logger.error(f"Error reading puzzle file: {e}")
            logger.info(f"Added {new_puzzles_count} new puzzles")
    else:
        logger.warning("No puzzles were generated")

    # Generate the FEN viewer
    generate_fen_viewer("output/puzzles.json", output_html="output/puzzles.html")


if __name__ == "__main__":
    logger.info("=== Starting Chess Divergence Puzzle Generator ===")
    args = parse_args()
    main(args.num_walks)
    logger.info("=== Finished Chess Divergence Puzzle Generator ===")
