# session_state_utils.py
"""Utilities for managing Streamlit session state."""

import streamlit as st

def initialize_session_state():
    """Initialize session state variables if they don't exist."""
    if "puzzle_index" not in st.session_state:
        st.session_state["puzzle_index"] = 0
    if "selected_cohort_pair" not in st.session_state:
        st.session_state["selected_cohort_pair"] = None
    # Add flag for Stockfish display
    if "show_stockfish" not in st.session_state:
        st.session_state["show_stockfish"] = False # Default to hidden

def clamp_puzzle_index(puzzle_ids):
    """
    Ensure puzzle_index is in [0, len(puzzle_ids)-1].
    If puzzle_ids is empty, puzzle_index stays 0 (handled later).
    """
    if not puzzle_ids: # Check if list is empty
        st.session_state["puzzle_index"] = 0
    else:
        max_index = len(puzzle_ids) - 1
        # Make sure puzzle_index exists before trying to access it
        current_index = st.session_state.get("puzzle_index", 0)
        st.session_state["puzzle_index"] = max(0, min(current_index, max_index))

def reset_stockfish_display_on_change():
    """Reset stockfish display when puzzle or cohort changes."""
    # Check if the flag exists before setting to False
    if "show_stockfish" in st.session_state:
         st.session_state.show_stockfish = False

def update_cohort_pair(new_cohort_pair):
    """Update the selected cohort pair in session state, resetting index and SF display if changed."""
    old_cohort_pair = st.session_state.get("selected_cohort_pair")
    if new_cohort_pair != old_cohort_pair:
        st.session_state["selected_cohort_pair"] = new_cohort_pair
        st.session_state["puzzle_index"] = 0 # Reset puzzle index
        reset_stockfish_display_on_change() # Reset SF display
    # Ensure it's set even if it's the same or first time
    st.session_state["selected_cohort_pair"] = new_cohort_pair

def update_puzzle_index(selected_puzzle_display_index):
    """Update the puzzle index based on user selection, resetting SF display if changed."""
    current_index = st.session_state.get("puzzle_index", 0)
    if current_index != selected_puzzle_display_index:
        st.session_state["puzzle_index"] = selected_puzzle_display_index
        reset_stockfish_display_on_change() # Reset SF display on direct selection change too

def toggle_stockfish_display():
    """Toggle the Stockfish analysis display flag."""
    st.session_state.show_stockfish = not st.session_state.get("show_stockfish", False)