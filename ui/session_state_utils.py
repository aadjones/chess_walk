# session_state_utils.py
"""Utilities for managing Streamlit session state."""

import streamlit as st

def initialize_session_state():
    """Initialize session state variables if they don't exist."""
    if "puzzle_index" not in st.session_state:
        st.session_state["puzzle_index"] = 0
    if "selected_cohort_pair" not in st.session_state:
        # Initialize later in the main flow or sidebar based on available data
        st.session_state["selected_cohort_pair"] = None

def clamp_puzzle_index(puzzle_ids):
    """
    Ensure puzzle_index is in [0, len(puzzle_ids)-1].
    If puzzle_ids is empty, puzzle_index stays 0 (handled later).
    """
    if not puzzle_ids: # Check if list is empty
        st.session_state["puzzle_index"] = 0
    else:
        max_index = len(puzzle_ids) - 1
        st.session_state["puzzle_index"] = max(0, min(st.session_state["puzzle_index"], max_index))

def update_cohort_pair(new_cohort_pair):
    """Update the selected cohort pair in session state, resetting index if changed."""
    old_cohort_pair = st.session_state.get("selected_cohort_pair")
    if new_cohort_pair != old_cohort_pair:
        st.session_state["selected_cohort_pair"] = new_cohort_pair
        st.session_state["puzzle_index"] = 0 # Reset puzzle index on cohort change
    # If it's the same, no state change needed here, main logic handles it.
    # Ensure it's set even if it's the first time or same as before
    st.session_state["selected_cohort_pair"] = new_cohort_pair


def update_puzzle_index(selected_puzzle_display_index):
    """Update the puzzle index based on user selection."""
    st.session_state["puzzle_index"] = selected_puzzle_display_index