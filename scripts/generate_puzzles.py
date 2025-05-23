import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pandas as pd
from dotenv import load_dotenv

from parameters import BASE_RATING, TARGET_RATING
from src.csv_utils import sort_csv
from src.logger import logger
from src.walker import generate_and_save_puzzles

load_dotenv()  # Load variables from .env file

# Ensure output directory exists
os.makedirs("output", exist_ok=True)


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: The parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Chess Divergence Puzzle Generator")
    parser.add_argument("--num_walks", type=int, default=10, help="Number of walks to generate (default: 10)")
    return parser.parse_args()


def count_puzzles(csv_path: str = "output/puzzles.csv") -> int:
    """
    Count the number of unique puzzles in the CSV file based on PuzzleIdx.

    Args:
        csv_path (str): Path to the CSV file.

    Returns:
        int: Number of unique puzzles.
    """
    if not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0:
        return 0  # Return 0 if file doesn't exist or is empty

    try:
        df = pd.read_csv(csv_path, index_col=[0, 1, 2])  # Expect three-level index: Cohort, Row, PuzzleIdx
        count = len(df.index.get_level_values("PuzzleIdx").unique())
        logger.debug(f"Counted {count} puzzles.")
        return count
    except Exception as e:
        logger.error(f"Error reading puzzles.csv: {e}. Assuming 0 puzzles.")
        return 0


def main(num_walks: int = 10) -> None:
    """
    Main function to orchestrate the puzzle generation process.

    Args:
        num_walks (int): Number of walks to generate.
    """
    logger.info(f"Starting puzzle generation with {num_walks} walks")
    logger.info(f"Base rating: {BASE_RATING}, Target rating: {TARGET_RATING}")

    # Migrate existing puzzles.csv to three-level index if needed
    if os.path.exists("output/puzzles.csv") and os.path.getsize("output/puzzles.csv") > 0:
        try:
            df = pd.read_csv("output/puzzles.csv")
            # Check if the CSV already has the correct three-level index
            if len(df.columns) > 0 and df.columns[0] != "Move":  # If first column isn't "Move", it has index columns
                df = pd.read_csv("output/puzzles.csv", index_col=[0, 1])
                if "PuzzleIdx" in df.columns:
                    df = df.reset_index()
                    df = df.set_index(["Cohort", "Row", "PuzzleIdx"])
                    df.to_csv("output/puzzles.csv")
                    logger.info("Migrated puzzles.csv to three-level index (Cohort, Row, PuzzleIdx).")
        except Exception as e:
            logger.warning(f"Failed to migrate puzzles.csv: {e}. Starting fresh.")
            os.remove("output/puzzles.csv")  # Remove corrupted file to start fresh

    # Count existing puzzles from the single CSV
    initial_puzzle_count = count_puzzles()
    logger.info(f"Found {initial_puzzle_count} existing puzzles")

    # Track new puzzles to report count at the end
    new_puzzles_count = 0
    for i in range(num_walks):
        logger.info(f"Generating walk {i+1}/{num_walks}")
        puzzles = generate_and_save_puzzles(BASE_RATING, TARGET_RATING)
        walk_puzzle_count = len(puzzles)
        new_puzzles_count += walk_puzzle_count
        logger.debug(f"Walk {i+1} added {walk_puzzle_count} puzzles. Running total: {new_puzzles_count}")
        if not puzzles:
            logger.warning(f"No puzzles generated for walk {i+1}")
            continue

    # Sort the puzzles.csv file by rating cohort pair
    sort_csv()
    logger.info("Sorted puzzles.csv by rating cohort pair")

    # Count total puzzles after generation
    total_puzzle_count = count_puzzles()
    logger.debug(
        f"Initial puzzles: {initial_puzzle_count}, New puzzles: {new_puzzles_count}, Total puzzles: {total_puzzle_count}"
    )

    if new_puzzles_count > 0:
        logger.info(f"Added {new_puzzles_count} new puzzles (total: {total_puzzle_count})")
    else:
        logger.warning("No new puzzles were generated")


if __name__ == "__main__":
    logger.info("=== Starting Chess Divergence Puzzle Generator ===")
    args = parse_args()
    main(num_walks=args.num_walks)
    logger.info("=== Finished Chess Divergence Puzzle Generator ===")
