# app.py
"""
Main Streamlit application file for exploring Chess Puzzle Cohort data.
Orchestrates data loading, UI, processing, and display.
"""
import os
import sys
import streamlit as st
import pandas as pd # Keep pandas for type hints or checks if needed

# --- Path Setup (Keep only if src/chess_utils is relative to app.py location) ---
# If chess_utils is importable directly (e.g., installed package or project structure), remove this.
# Assuming src/ is one level up from where app.py is located. Adjust as needed.
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
# Note: puzzle_logic.py already handles its own path insertion for chess_utils

# --- Page Configuration ---
st.set_page_config(layout="wide", page_title="Chess Puzzle Explorer")

# --- Import Modularized Functions ---
from config import COL_FEN, BASE_COHORT_ID, TARGET_COHORT_ID # Import needed constants
from data_loader import (
    load_puzzle_data,
    get_unique_cohort_pairs,
    filter_data_by_cohort_pair,
    group_by_puzzle_index,
)
from session_state_utils import initialize_session_state
from sidebar import create_cohort_pair_selector, create_puzzle_controls
from puzzle_logic import get_puzzle_data, prepare_board_data, convert_moves_to_san
from data_formatting import (
    cleanup_dataframe,
    format_wdl_column,
    infer_rating,
    prepare_display_dataframe,
)
from display import layout_main_content

def main():
    """Main function to orchestrate the app workflow."""
    st.title("Chess Puzzle Cohort Analysis")

    # --- Initialization ---
    initialize_session_state() # Must be called early
    puzzles_df = load_puzzle_data() # Load data once

    if puzzles_df is None or puzzles_df.empty:
        st.error("Failed to load puzzle data. Application cannot continue.")
        st.stop()

    unique_pairs = get_unique_cohort_pairs(puzzles_df)
    if not unique_pairs:
        st.warning("No Cohort Pairs found in the data.")
        st.stop()

    # --- Sidebar / User Input ---
    # Cohort Pair selection (updates session state internally)
    selected_cohort_pair = create_cohort_pair_selector(unique_pairs)
    if selected_cohort_pair is None:
         st.stop() # Stop if selector failed or returned None

    # --- Data Filtering & Grouping based on Sidebar Input ---
    filtered_df = filter_data_by_cohort_pair(puzzles_df, selected_cohort_pair)
    if filtered_df.empty:
        st.warning(f"No data found for Cohort Pair: {selected_cohort_pair}")
        # Clear sidebar puzzle controls if no data
        create_puzzle_controls([]) # Pass empty list
        st.stop()

    puzzle_groups, puzzle_ids = group_by_puzzle_index(filtered_df)
    if not puzzle_ids:
        st.warning(f"No puzzles found for Cohort Pair: {selected_cohort_pair}")
        # Clear sidebar puzzle controls if no puzzles
        create_puzzle_controls([]) # Pass empty list
        st.stop()

    # Puzzle selection (updates session state internally, returns current ID)
    current_puzzle_id = create_puzzle_controls(puzzle_ids)
    if current_puzzle_id is None:
        # This happens if puzzle_ids was empty, handled above, but good practice check
        st.info("Select a puzzle from the sidebar.")
        st.stop()

    # --- Puzzle Processing ---
    puzzle_df = get_puzzle_data(puzzle_groups, current_puzzle_id)
    if puzzle_df is None or puzzle_df.empty:
        st.warning(f"Could not retrieve data for Puzzle ID: {current_puzzle_id}")
        st.stop()

    fen = puzzle_df[COL_FEN].iloc[0] # Get FEN early for use in SAN conversion

    board, svg_board, base_data_raw, target_data_raw = prepare_board_data(puzzle_df)

    # We need the original rating before cleanup
    base_rating = infer_rating(base_data_raw, BASE_COHORT_ID.capitalize())
    target_rating = infer_rating(target_data_raw, TARGET_COHORT_ID.capitalize())

    # Convert moves before cleaning up columns
    base_data_sanned, target_data_sanned = convert_moves_to_san(base_data_raw, target_data_raw, fen)

    # --- Data Formatting for Display ---
    base_data_cleaned = cleanup_dataframe(base_data_sanned)
    target_data_cleaned = cleanup_dataframe(target_data_sanned)

    base_data_wdl = format_wdl_column(base_data_cleaned)
    target_data_wdl = format_wdl_column(target_data_cleaned)

    base_display_df = prepare_display_dataframe(base_data_wdl)
    target_display_df = prepare_display_dataframe(target_data_wdl)

    # --- Display Layout ---
    layout_main_content(fen, svg_board, base_rating, target_rating, base_display_df, target_display_df)


if __name__ == "__main__":
    main()