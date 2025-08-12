# app.py
"""
Main Streamlit application file for exploring Chess Position Cohort data.
Orchestrates data loading, UI, processing, and display, including Stockfish analysis.
"""
import streamlit as st
import pandas as pd

# --- Page Configuration (should be first Streamlit command) ---
st.set_page_config(layout="wide", page_title="Chess Position Explorer")

# --- Import Modules ---
# Configuration (loads and validates on import)
from config import settings

# Data Loading
from data_loader import (
    load_position_data,
    get_unique_cohort_pairs,
    filter_data_by_cohort_pair,
    group_by_position_index,
)

# Session State Management
from session_state_utils import initialize_session_state

# UI Components
from sidebar import create_cohort_pair_selector, create_position_controls
from display import layout_main_content # Imports the layout function

# Core Logic
from puzzle_logic import (
    get_position_data,
    prepare_board_data,
    convert_moves_to_san,
    get_stockfish_analysis # Imports the analysis function
)

# Data Formatting
from data_formatting import (
    cleanup_dataframe,
    format_wdl_column,
    infer_rating,
    prepare_display_dataframe,
)

# --- Main Application Logic ---

def main():
    """Main function to orchestrate the app workflow."""
    st.title("Chess Position Cohort Analysis")

    # --- Initialization ---
    initialize_session_state()
    positions_df = load_position_data()

    if positions_df is None or positions_df.empty:
        st.error("Failed to load position data. Application cannot continue.")
        st.stop()

    unique_pairs = get_unique_cohort_pairs(positions_df)
    if not unique_pairs:
        st.warning("No Cohort Pairs found in the data.")
        st.stop()

    # --- Sidebar / User Input ---
    selected_cohort_pair = create_cohort_pair_selector(unique_pairs)
    if selected_cohort_pair is None:
         st.stop()

    # --- Data Filtering & Grouping ---
    filtered_df = filter_data_by_cohort_pair(positions_df, selected_cohort_pair)
    if filtered_df.empty:
        st.warning(f"No position data found for Cohort Pair: {selected_cohort_pair}")
        create_position_controls([])
        st.stop()

    position_groups, position_ids = group_by_position_index(filtered_df)
    if not position_ids:
        st.warning(f"No positions found for Cohort Pair: {selected_cohort_pair}")
        create_position_controls([])
        st.stop()

    current_position_id = create_position_controls(position_ids)
    if current_position_id is None:
        st.info("Select a position from the sidebar.")
        st.stop()

    # --- Position Processing ---
    position_df = get_position_data(position_groups, current_position_id)
    if position_df is None or position_df.empty:
        st.stop()

    if settings.col_fen not in position_df.columns:
        st.error(f"Critical Error: '{settings.col_fen}' column missing.")
        st.stop()
    fen = position_df[settings.col_fen].iloc[0]

    # Prepare board data AND get raw UCI moves needed for Stockfish
    board, svg_board, base_data_raw, target_data_raw, base_uci, target_uci = prepare_board_data(position_df)

    # --- Data Formatting ---
    base_rating = infer_rating(base_data_raw, settings.base_cohort_id.capitalize())
    target_rating = infer_rating(target_data_raw, settings.target_cohort_id.capitalize())
    base_data_sanned, target_data_sanned = convert_moves_to_san(base_data_raw.copy(), target_data_raw.copy(), fen)
    base_data_cleaned = cleanup_dataframe(base_data_sanned)
    target_data_cleaned = cleanup_dataframe(target_data_sanned)
    base_data_wdl = format_wdl_column(base_data_cleaned)
    target_data_wdl = format_wdl_column(target_data_cleaned)
    base_display_df = prepare_display_dataframe(base_data_wdl)
    target_display_df = prepare_display_dataframe(target_data_wdl)

    # --- Stockfish Analysis (Run only if requested) ---
    stockfish_results = None # Initialize
    if st.session_state.get("show_stockfish", False):
         stockfish_results = get_stockfish_analysis(fen, base_uci, target_uci)

    # --- Display Layout ---
    layout_main_content(
        fen=fen,
        svg_board=svg_board,
        base_rating=base_rating,
        target_rating=target_rating,
        base_display_df=base_display_df,
        target_display_df=target_display_df,
        stockfish_results=stockfish_results # Pass the analysis results dict
    )


if __name__ == "__main__":
    main()