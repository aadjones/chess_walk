# data_loader.py
"""Handles loading data for the application."""

import pandas as pd
import streamlit as st
# Import the single settings instance
from config import settings

@st.cache_data # Cache the data loading
def load_puzzle_data():
    """Load the entire puzzles CSV as a DataFrame (unfiltered)."""
    csv_path = settings.puzzles_csv_path
    try:
        # Don't set index_col here; keep all columns.
        puzzles_df = pd.read_csv(csv_path)
        # Basic validation
        if puzzles_df.empty:
            st.warning(f"Warning: Puzzle file loaded but is empty: '{csv_path}'")
        required_cols = [settings.col_cohort_pair, settings.col_puzzle_idx, settings.col_fen]
        missing_cols = [col for col in required_cols if col not in puzzles_df.columns]
        if missing_cols:
            st.error(f"Error: Missing required columns in '{csv_path}': {', '.join(missing_cols)}")
            return None # Return None to indicate critical error
        return puzzles_df
    except FileNotFoundError:
        st.error(f"Error: The puzzle file was not found at '{csv_path}'.")
        st.stop() # Stop execution if data isn't loaded
    except pd.errors.EmptyDataError:
         st.error(f"Error: The puzzle file at '{csv_path}' is empty.")
         st.stop()
    except Exception as e:
        st.error(f"An error occurred while loading or parsing the puzzle data from '{csv_path}': {e}")
        st.stop()


def get_unique_cohort_pairs(puzzles_df):
    """Get sorted unique CohortPair values from the DataFrame."""
    if puzzles_df is None or puzzles_df.empty:
        return []
    cohort_pair_col = settings.col_cohort_pair
    if cohort_pair_col not in puzzles_df.columns:
         st.error(f"Error: '{cohort_pair_col}' column not found in the data.")
         return []
    try:
        return sorted(puzzles_df[cohort_pair_col].unique())
    except Exception as e:
        st.error(f"Error processing unique cohort pairs: {e}")
        return []

def filter_data_by_cohort_pair(puzzles_df, selected_cohort_pair):
    """Filter the DataFrame by the selected CohortPair."""
    if puzzles_df is None or puzzles_df.empty or selected_cohort_pair is None:
        return pd.DataFrame() # Return empty df if input is invalid
    cohort_pair_col = settings.col_cohort_pair
    if cohort_pair_col not in puzzles_df.columns:
        # This error should ideally be caught earlier, but good failsafe
        return pd.DataFrame()
    return puzzles_df[puzzles_df[cohort_pair_col] == selected_cohort_pair].copy()


def group_by_puzzle_index(filtered_df):
    """Group the filtered DataFrame by PuzzleIdx."""
    if filtered_df.empty:
        return None, []
    puzzle_idx_col = settings.col_puzzle_idx
    if puzzle_idx_col not in filtered_df.columns:
        st.error(f"Error: '{puzzle_idx_col}' column not found in the data.")
        return None, []

    try:
        puzzle_groups = filtered_df.groupby(puzzle_idx_col)
        puzzle_ids = sorted(list(puzzle_groups.groups.keys()))
        return puzzle_groups, puzzle_ids
    except Exception as e:
        st.error(f"Error grouping data by puzzle index: {e}")
        return None, []