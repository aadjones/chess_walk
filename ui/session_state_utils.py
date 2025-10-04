# session_state_utils.py
"""Utilities for managing Streamlit session state."""

import streamlit as st


def initialize_session_state():
    """Initialize session state variables if they don't exist.

    Single source of truth: (cohort_filter, position_index)
    - cohort_filter: Currently selected cohort pair
    - position_index: 0-based index within that cohort
    """
    if "cohort_filter" not in st.session_state:
        st.session_state["cohort_filter"] = "1400-1800"
    if "position_index" not in st.session_state:
        st.session_state["position_index"] = 0
    if "show_stockfish" not in st.session_state:
        st.session_state["show_stockfish"] = False


def toggle_stockfish_display():
    """Toggle the Stockfish analysis display flag."""
    st.session_state.show_stockfish = not st.session_state.get("show_stockfish", False)
