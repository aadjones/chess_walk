# data_loader.py
"""Handles loading data for the application."""

import pandas as pd
import streamlit as st
# Import the single settings instance
from config import settings

@st.cache_data(ttl=60) # Cache with 60 second TTL to force refresh  
def load_position_data():
    """Load the entire positions CSV as a DataFrame (unfiltered)."""
    csv_path = settings.positions_csv_path
    
    # Add file modification time to force cache refresh when file changes
    import os
    file_mtime = os.path.getmtime(csv_path) if os.path.exists(csv_path) else 0
    # Use mtime in cache key but don't display it
    
    try:
        # Don't set index_col here; keep all columns.
        positions_df = pd.read_csv(csv_path)
        # Basic validation
        if positions_df.empty:
            st.warning(f"Warning: Position file loaded but is empty: '{csv_path}'")
        
        required_cols = [settings.col_cohort_pair, settings.col_position_idx, settings.col_fen]
        missing_cols = [col for col in required_cols if col not in positions_df.columns]
        if missing_cols:
            st.error(f"Error: Missing required columns in '{csv_path}': {', '.join(missing_cols)}")
            return None # Return None to indicate critical error
        return positions_df
    except FileNotFoundError:
        st.error(f"Error: The position file was not found at '{csv_path}'.")
        st.stop() # Stop execution if data isn't loaded
    except pd.errors.EmptyDataError:
         st.error(f"Error: The position file at '{csv_path}' is empty.")
         st.stop()
    except Exception as e:
        st.error(f"An error occurred while loading or parsing the position data from '{csv_path}': {e}")
        st.stop()


def get_unique_cohort_pairs(positions_df):
    """Get sorted unique CohortPair values from the DataFrame."""
    if positions_df is None or positions_df.empty:
        return []
    cohort_pair_col = settings.col_cohort_pair
    if cohort_pair_col not in positions_df.columns:
         st.error(f"Error: '{cohort_pair_col}' column not found in the data.")
         return []
    try:
        return sorted(positions_df[cohort_pair_col].unique())
    except Exception as e:
        st.error(f"Error processing unique cohort pairs: {e}")
        return []

def filter_data_by_cohort_pair(positions_df, selected_cohort_pair):
    """Filter the DataFrame by the selected CohortPair."""
    if positions_df is None or positions_df.empty or selected_cohort_pair is None:
        return pd.DataFrame() # Return empty df if input is invalid
    cohort_pair_col = settings.col_cohort_pair
    if cohort_pair_col not in positions_df.columns:
        # This error should ideally be caught earlier, but good failsafe
        return pd.DataFrame()
    return positions_df[positions_df[cohort_pair_col] == selected_cohort_pair].copy()


def group_by_position_index(filtered_df):
    """Group the filtered DataFrame by PositionIdx."""
    if filtered_df.empty:
        return None, []
    position_idx_col = settings.col_position_idx
    if position_idx_col not in filtered_df.columns:
        st.error(f"Error: '{position_idx_col}' column not found in the data.")
        return None, []

    try:
        position_groups = filtered_df.groupby(position_idx_col)
        position_ids = sorted(list(position_groups.groups.keys()))
        return position_groups, position_ids
    except Exception as e:
        st.error(f"Error grouping data by position index: {e}")
        return None, []