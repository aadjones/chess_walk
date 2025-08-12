#!/usr/bin/env python3
"""
Script to reorganize positions.csv for better user experience:
1. Order positions by lower rating cohort (ascending)
2. Renumber positions starting from 1 (instead of 0)
3. Maintain the three-level index structure (Cohort, Row, PositionIdx)
"""

import os
import sys
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.logger import logger


def extract_lower_rating(cohort_pair: str) -> int:
    """Extract the lower rating from a cohort pair string like '1000-1400'."""
    try:
        ratings = cohort_pair.split("-")
        return int(ratings[0])
    except (ValueError, IndexError):
        logger.warning(f"Could not parse cohort pair: {cohort_pair}")
        return 0


def reorganize_positions_csv(
    input_path: str = "output/positions.csv", output_path: str = "output/positions_reorganized.csv"
) -> None:
    """
    Reorganize the positions CSV file for better user experience.
    """
    logger.info("Starting position reorganization...")

    # Load the existing CSV
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        return

    try:
        df = pd.read_csv(input_path, index_col=[0, 1, 2])  # Cohort, Row, PositionIdx
        logger.info(f"Loaded {len(df.index.get_level_values('PositionIdx').unique())} existing positions")
    except Exception as e:
        logger.error(f"Error loading CSV: {e}")
        return

    # Reset index to work with the data as regular columns
    df_reset = df.reset_index()

    # Extract lower rating for sorting
    df_reset["lower_rating"] = df_reset["CohortPair"].apply(extract_lower_rating)

    # Get unique positions (one row per position for sorting)
    unique_positions = df_reset[["PositionIdx", "CohortPair", "lower_rating"]].drop_duplicates()

    # Sort by lower rating, then by original PositionIdx as tiebreaker
    unique_positions_sorted = unique_positions.sort_values(["lower_rating", "PositionIdx"])

    # Create mapping from old PositionIdx to new PositionIdx (starting from 1)
    old_to_new_mapping = {}
    for i, (_, row) in enumerate(unique_positions_sorted.iterrows()):
        old_idx = row["PositionIdx"]
        new_idx = i + 1  # Start from 1 instead of 0
        old_to_new_mapping[old_idx] = new_idx

    logger.info(f"Created mapping for {len(old_to_new_mapping)} positions")

    # Apply the mapping to the full dataset
    df_reset["new_PositionIdx"] = df_reset["PositionIdx"].map(old_to_new_mapping)

    # Drop the temporary column and replace PositionIdx
    df_reset = df_reset.drop(columns=["PositionIdx", "lower_rating"])
    df_reset = df_reset.rename(columns={"new_PositionIdx": "PositionIdx"})

    # Recreate the three-level index
    df_final = df_reset.set_index(["Cohort", "Row", "PositionIdx"])

    # Sort by the new index to ensure proper ordering
    df_final = df_final.sort_index()

    # Save the reorganized CSV
    df_final.to_csv(output_path)
    logger.info(f"Saved reorganized positions to: {output_path}")

    # Log the reorganization summary
    new_unique_positions = df_final.index.get_level_values("PositionIdx").unique()
    logger.info(f"Reorganized {len(new_unique_positions)} positions")
    logger.info(f"New position range: {min(new_unique_positions)} to {max(new_unique_positions)}")

    # Show a sample of the cohort pair ordering
    cohort_pairs_ordered = df_final.reset_index()["CohortPair"].drop_duplicates()
    logger.info(f"Cohort pair ordering: {list(cohort_pairs_ordered)[:5]}...")


def main():
    """Main function."""
    logger.info("=== Starting Position Reorganization ===")

    # Create backup first
    backup_path = "output/positions_before_reorganization.csv"
    if os.path.exists("output/positions.csv"):
        import shutil

        shutil.copy2("output/positions.csv", backup_path)
        logger.info(f"Created backup at: {backup_path}")

    # Reorganize positions
    reorganize_positions_csv()

    # Replace the original file
    if os.path.exists("output/positions_reorganized.csv"):
        import shutil

        shutil.move("output/positions_reorganized.csv", "output/positions.csv")
        logger.info("Replaced original positions.csv with reorganized version")

    logger.info("=== Position Reorganization Complete ===")


if __name__ == "__main__":
    main()
