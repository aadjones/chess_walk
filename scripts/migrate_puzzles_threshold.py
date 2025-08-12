#!/usr/bin/env python3
"""
Migration script to clean existing puzzles.csv with the new MIN_WIN_RATE_DELTA threshold.

This script reads existing puzzles, re-evaluates each one with the corrected 5.0 percentage point
threshold, and keeps only puzzles that represent genuine rating-based divergences.
"""

import os
import sys
import pandas as pd
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from parameters import MIN_WIN_RATE_DELTA
from src.logger import logger


def load_existing_puzzles(csv_path: str = "output/puzzles.csv") -> pd.DataFrame:
    """Load existing puzzles CSV with proper indexing."""
    if not os.path.exists(csv_path):
        logger.warning(f"No existing puzzles file found at {csv_path}")
        return pd.DataFrame()
    
    try:
        df = pd.read_csv(csv_path, index_col=[0, 1, 2])  # Cohort, Row, PuzzleIdx
        logger.info(f"Loaded {len(df.index.get_level_values('PuzzleIdx').unique())} existing puzzles")
        return df
    except Exception as e:
        logger.error(f"Error loading puzzles CSV: {e}")
        return pd.DataFrame()


def extract_puzzle_moves_and_stats(puzzle_group: pd.DataFrame) -> Tuple[Dict, Dict]:
    """Extract move statistics for base and target cohorts from a puzzle group."""
    base_data = puzzle_group.loc['base'].copy()
    target_data = puzzle_group.loc['target'].copy()
    
    # Build move dictionaries with win rates as percentages (0-100)
    base_moves = {}
    target_moves = {}
    
    for _, row in base_data.iterrows():
        base_moves[row['Move']] = {
            'win_rate': row['White %'],
            'games': row['Games'],
            'freq': row['Freq']
        }
    
    for _, row in target_data.iterrows():
        target_moves[row['Move']] = {
            'win_rate': row['White %'],
            'games': row['Games'], 
            'freq': row['Freq']
        }
    
    return base_moves, target_moves


def evaluate_puzzle_with_new_threshold(base_moves: Dict, target_moves: Dict) -> bool:
    """
    Re-evaluate a puzzle using the new MIN_WIN_RATE_DELTA threshold.
    
    Returns True if the puzzle still meets the stricter criteria.
    """
    if not base_moves or not target_moves:
        return False
    
    # Get top moves by frequency
    base_top_move = max(base_moves.keys(), key=lambda m: base_moves[m]['freq'])
    target_top_move = max(target_moves.keys(), key=lambda m: target_moves[m]['freq'])
    
    # If same top move, no divergence
    if base_top_move == target_top_move:
        return False
    
    # Check if target's top move exists in base cohort data
    if target_top_move not in base_moves:
        return False
    
    # Get win rates (already in percentage format 0-100)
    base_top_win_rate = base_moves[base_top_move]['win_rate']
    base_win_rate_for_target_move = base_moves[target_top_move]['win_rate']
    base_games_for_target_move = base_moves[target_top_move]['games']
    
    # Check if target move significantly outperforms base top move in base cohort
    win_rate_delta = base_win_rate_for_target_move - base_top_win_rate
    min_games_threshold = 5
    
    meets_threshold = (
        win_rate_delta >= MIN_WIN_RATE_DELTA and 
        base_games_for_target_move >= min_games_threshold
    )
    
    if meets_threshold:
        logger.debug(
            f"Puzzle PASSES: {target_top_move} vs {base_top_move}, "
            f"delta={win_rate_delta:.1f}% (threshold={MIN_WIN_RATE_DELTA}%), "
            f"games={base_games_for_target_move}"
        )
    else:
        logger.debug(
            f"Puzzle FAILS: {target_top_move} vs {base_top_move}, "
            f"delta={win_rate_delta:.1f}% (threshold={MIN_WIN_RATE_DELTA}%), "
            f"games={base_games_for_target_move}"
        )
    
    return meets_threshold


def migrate_puzzles(input_path: str = "output/puzzles.csv", 
                   output_path: str = "output/puzzles_migrated.csv",
                   backup_path: str = "output/puzzles_backup.csv") -> None:
    """
    Migrate existing puzzles by filtering with new threshold.
    """
    logger.info(f"Starting puzzle migration with MIN_WIN_RATE_DELTA = {MIN_WIN_RATE_DELTA}%")
    
    # Load existing puzzles
    df = load_existing_puzzles(input_path)
    if df.empty:
        logger.warning("No puzzles to migrate")
        return
    
    # Create backup
    df.to_csv(backup_path)
    logger.info(f"Created backup at {backup_path}")
    
    # Get unique puzzle indices
    puzzle_indices = df.index.get_level_values('PuzzleIdx').unique()
    total_puzzles = len(puzzle_indices)
    logger.info(f"Evaluating {total_puzzles} puzzles...")
    
    valid_puzzles = []
    rejected_puzzles = []
    
    for puzzle_idx in puzzle_indices:
        try:
            # Get puzzle data for this index
            puzzle_group = df.xs(puzzle_idx, level='PuzzleIdx')
            
            # Extract move statistics
            base_moves, target_moves = extract_puzzle_moves_and_stats(puzzle_group)
            
            # Re-evaluate with new threshold
            if evaluate_puzzle_with_new_threshold(base_moves, target_moves):
                valid_puzzles.append(puzzle_idx)
            else:
                rejected_puzzles.append(puzzle_idx)
                
        except Exception as e:
            logger.warning(f"Error processing puzzle {puzzle_idx}: {e}")
            rejected_puzzles.append(puzzle_idx)
    
    # Filter dataframe to keep only valid puzzles
    if valid_puzzles:
        filtered_df = df[df.index.get_level_values('PuzzleIdx').isin(valid_puzzles)]
        
        # Reassign puzzle indices to be sequential starting from 0
        unique_valid_indices = sorted(valid_puzzles)
        index_mapping = {old_idx: new_idx for new_idx, old_idx in enumerate(unique_valid_indices)}
        
        # Reset and rebuild index with new PuzzleIdx values
        filtered_df = filtered_df.reset_index()
        filtered_df['PuzzleIdx'] = filtered_df['PuzzleIdx'].map(index_mapping)
        filtered_df = filtered_df.set_index(['Cohort', 'Row', 'PuzzleIdx'])
        
        # Save migrated puzzles
        filtered_df.to_csv(output_path)
        logger.info(
            f"Migration complete! Kept {len(valid_puzzles)} puzzles, "
            f"rejected {len(rejected_puzzles)} puzzles "
            f"({len(rejected_puzzles)/total_puzzles*100:.1f}% rejection rate)"
        )
        logger.info(f"Migrated puzzles saved to {output_path}")
        
    else:
        logger.warning("No puzzles met the new threshold criteria!")
        # Create empty file to indicate migration completed
        pd.DataFrame().to_csv(output_path)


def main():
    """Main migration function."""
    logger.info("=== Starting Puzzle Threshold Migration ===")
    
    migrate_puzzles()
    
    logger.info("=== Puzzle Migration Complete ===")


if __name__ == "__main__":
    main()