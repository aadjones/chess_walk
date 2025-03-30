# data_loader.py
"""Handles loading data for the application."""

import pandas as pd
import streamlit as st
from config import PUZZLES_CSV_PATH # Use config

@st.cache_data # Cache the data loading
def load_puzzle_data():
    """Load the entire puzzles CSV as a DataFrame (unfiltered)."""
    try:
        # Don't set index_col here; keep all columns.
        puzzles_df = pd.read_csv(PUZZLES_CSV_PATH)
        return puzzles_df
    except FileNotFoundError:
        st.error(f"Error: The puzzle file was not found at '{PUZZLES_CSV_PATH}'.")
        st.stop() # Stop execution if data isn't loaded
    except Exception as e:
        st.error(f"An error occurred while loading the puzzle data: {e}")
        st.stop()

def get_unique_cohort_pairs(puzzles_df):
    """Get sorted unique CohortPair values from the DataFrame."""
    if puzzles_df is None or puzzles_df.empty:
        return []
    if "CohortPair" not in puzzles_df.columns:
         st.error("Error: 'CohortPair' column not found in the data.")
         return []
    return sorted(puzzles_df["CohortPair"].unique())

def filter_data_by_cohort_pair(puzzles_df, selected_cohort_pair):
    """Filter the DataFrame by the selected CohortPair."""
    if puzzles_df is None or selected_cohort_pair is None:
        return pd.DataFrame() # Return empty df if input is invalid
    return puzzles_df[puzzles_df["CohortPair"] == selected_cohort_pair]

def group_by_puzzle_index(filtered_df):
    """Group the filtered DataFrame by PuzzleIdx."""
    if filtered_df.empty:
        return None, []
    if "PuzzleIdx" not in filtered_df.columns:
        st.error("Error: 'PuzzleIdx' column not found in the data.")
        return None, []

    puzzle_groups = filtered_df.groupby("PuzzleIdx")
    puzzle_ids = sorted(list(puzzle_groups.groups.keys()))
    return puzzle_groups, puzzle_ids