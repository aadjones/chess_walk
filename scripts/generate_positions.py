import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pandas as pd
from dotenv import load_dotenv

from parameters import BASE_RATING, TARGET_RATING
from src.csv_utils import sort_csv
from src.logger import logger
from src.walker import generate_and_save_positions

load_dotenv()  # Load variables from .env file

# Ensure output directory exists
os.makedirs("output", exist_ok=True)


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: The parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Chess Divergence Position Generator")
    parser.add_argument("--num_walks", type=int, default=10, help="Number of walks to generate (default: 10)")
    return parser.parse_args()


def count_positions(csv_path: str = "output/positions.csv") -> int:
    """
    Count the number of unique positions in the CSV file based on PositionIdx.

    Args:
        csv_path (str): Path to the CSV file.

    Returns:
        int: Number of unique positions.
    """
    if not os.path.exists(csv_path) or os.path.getsize(csv_path) == 0:
        return 0  # Return 0 if file doesn't exist or is empty

    try:
        df = pd.read_csv(csv_path, index_col=[0, 1, 2])  # Expect three-level index: Cohort, Row, PositionIdx
        count = len(df.index.get_level_values("PositionIdx").unique())
        logger.debug(f"Counted {count} positions.")
        return count
    except Exception as e:
        logger.error(f"Error reading positions.csv: {e}. Assuming 0 positions.")
        return 0


def main(num_walks: int = 10) -> None:
    """
    Main function to orchestrate the position generation process.

    Args:
        num_walks (int): Number of walks to generate.
    """
    logger.info(f"Starting position generation with {num_walks} walks")
    logger.info(f"Base rating: {BASE_RATING}, Target rating: {TARGET_RATING}")

    # Migrate existing positions.csv to three-level index if needed
    if os.path.exists("output/positions.csv") and os.path.getsize("output/positions.csv") > 0:
        try:
            df = pd.read_csv("output/positions.csv")
            # Check if the CSV already has the correct three-level index
            if len(df.columns) > 0 and df.columns[0] != "Move":  # If first column isn't "Move", it has index columns
                df = pd.read_csv("output/positions.csv", index_col=[0, 1])
                if "PositionIdx" in df.columns:
                    df = df.reset_index()
                    df = df.set_index(["Cohort", "Row", "PositionIdx"])
                    df.to_csv("output/positions.csv")
                    logger.info("Migrated positions.csv to three-level index (Cohort, Row, PositionIdx).")
        except Exception as e:
            logger.warning(f"Failed to migrate positions.csv: {e}. Starting fresh.")
            os.remove("output/positions.csv")  # Remove corrupted file to start fresh

    # Count existing positions from the single CSV
    initial_puzzle_count = count_positions()
    logger.info(f"Found {initial_puzzle_count} existing positions")

    # Track new positions to report count at the end
    new_positions_count = 0
    for i in range(num_walks):
        logger.info(f"Generating walk {i+1}/{num_walks}")
        positions = generate_and_save_positions(BASE_RATING, TARGET_RATING)
        walk_puzzle_count = len(positions)
        new_positions_count += walk_puzzle_count
        logger.debug(f"Walk {i+1} added {walk_puzzle_count} positions. Running total: {new_positions_count}")
        if not positions:
            logger.warning(f"No positions generated for walk {i+1}")
            continue

    # Sort the positions.csv file by rating cohort pair
    sort_csv()
    logger.info("Sorted positions.csv by rating cohort pair")

    # Reorganize positions to maintain proper numbering sequence
    if new_positions_count > 0:
        logger.info("Reorganizing positions to maintain sequential numbering...")
        # Import and run reorganization logic directly
        sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
        from reorganize_positions import reorganize_positions_csv

        reorganize_positions_csv()
        logger.info("Positions reorganized with proper sequential numbering")

    # Count total positions after generation
    total_puzzle_count = count_positions()
    logger.debug(
        f"Initial positions: {initial_puzzle_count}, New positions: {new_positions_count}, Total positions: {total_puzzle_count}"
    )

    if new_positions_count > 0:
        logger.info(f"Added {new_positions_count} new positions (total: {total_puzzle_count})")
    else:
        logger.warning("No new positions were generated")


if __name__ == "__main__":
    logger.info("=== Starting Chess Divergence Position Generator ===")
    args = parse_args()
    main(num_walks=args.num_walks)
    logger.info("=== Finished Chess Divergence Position Generator ===")
