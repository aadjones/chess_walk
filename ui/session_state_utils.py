# session_state_utils.py
"""Utilities for managing Streamlit session state."""

import streamlit as st

def initialize_session_state():
    """Initialize session state variables if they don't exist."""
    if "position_index" not in st.session_state:
        st.session_state["position_index"] = 0
    if "selected_cohort_pair" not in st.session_state:
        st.session_state["selected_cohort_pair"] = "1400-1800"
    # Add flag for Stockfish display
    if "show_stockfish" not in st.session_state:
        st.session_state["show_stockfish"] = False # Default to hidden

def clamp_position_index(position_ids):
    """
    Ensure position_index is in [0, len(position_ids)-1].
    If position_ids is empty, position_index stays 0 (handled later).
    """
    if not position_ids: # Check if list is empty
        st.session_state["position_index"] = 0
    else:
        max_index = len(position_ids) - 1
        # Make sure position_index exists before trying to access it
        current_index = st.session_state.get("position_index", 0)
        st.session_state["position_index"] = max(0, min(current_index, max_index))

def reset_stockfish_display_on_change():
    """Reset stockfish display when position or cohort changes."""
    # Check if the flag exists before setting to False
    if "show_stockfish" in st.session_state:
         st.session_state.show_stockfish = False

def update_cohort_pair(new_cohort_pair):
    """Update the selected cohort pair in session state, resetting index and SF display if changed."""
    old_cohort_pair = st.session_state.get("selected_cohort_pair")
    if new_cohort_pair != old_cohort_pair:
        st.session_state["selected_cohort_pair"] = new_cohort_pair
        # Check if we have a requested position, otherwise reset to 0
        if "requested_position_id" not in st.session_state:
            st.session_state["position_index"] = 0 # Reset position index
        reset_stockfish_display_on_change() # Reset SF display
        # Force rerun to update filtered data immediately
        st.rerun()
    # Ensure it's set even if it's the same or first time
    st.session_state["selected_cohort_pair"] = new_cohort_pair

def update_position_index(selected_position_display_index):
    """Update the position index based on user selection, resetting SF display if changed."""
    current_index = st.session_state.get("position_index", 0)
    if current_index != selected_position_display_index:
        st.session_state["position_index"] = selected_position_display_index
        reset_stockfish_display_on_change() # Reset SF display on direct selection change too
        # Remove st.rerun() - it's causing dropdown selection issues

def toggle_stockfish_display():
    """Toggle the Stockfish analysis display flag."""
    st.session_state.show_stockfish = not st.session_state.get("show_stockfish", False)