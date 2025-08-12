# sidebar.py
"""Handles the creation and logic of the Streamlit sidebar."""

import streamlit as st
from session_state_utils import clamp_position_index, update_cohort_pair, update_position_index
from config import settings # Import settings if needed for labels, though not strictly required here currently

def create_cohort_pair_selector(unique_pairs):
    """Create the selectbox for choosing a Cohort Pair."""
    st.sidebar.subheader("Select Cohort Pair") # Use subheader for better grouping
    if not unique_pairs:
        st.sidebar.warning("No Cohort Pairs found in data.")
        return None

    # Determine default index safely
    current_selection = st.session_state.get("selected_cohort_pair")
    # If no selection yet or invalid, default to first item
    if current_selection not in unique_pairs:
         current_selection = unique_pairs[0]

    try:
        default_index = unique_pairs.index(current_selection)
    except ValueError:
        default_index = 0 # Fallback just in case

    new_cohort_pair = st.sidebar.selectbox(
        "Cohort Pair:", # Shorten label
        unique_pairs,
        index=default_index,
        key="cohort_pair_selector", # Add key for stability
        label_visibility="collapsed" # Hide label if subheader is enough
    )
    # update_cohort_pair handles session state logic
    update_cohort_pair(new_cohort_pair)
    return st.session_state["selected_cohort_pair"]


def create_position_controls(position_ids):
    """Create sidebar controls for position navigation and return the chosen position ID."""
    st.sidebar.title("Position Controls")

    num_positions = len(position_ids)
    # Ensure index exists and is valid before accessing
    current_index = st.session_state.get("position_index", 0)
    if num_positions > 0:
        current_index = max(0, min(current_index, num_positions - 1))
    else:
        current_index = 0


    # --- Navigation Buttons ---
    st.sidebar.caption(f"Position {current_index + 1} of {num_positions}" if num_positions > 0 else "No positions")
    col1, col2 = st.sidebar.columns(2)

    # Disable buttons appropriately
    disable_prev = (current_index <= 0)
    disable_next = (current_index >= num_positions - 1)

    def prev_position():
        if st.session_state["position_index"] > 0:
            st.session_state["position_index"] -= 1
            # Need to reset Stockfish display when navigating with buttons too
            if "show_stockfish" in st.session_state:
                st.session_state.show_stockfish = False

    def next_position():
        if st.session_state["position_index"] < num_positions - 1:
            st.session_state["position_index"] += 1
            # Need to reset Stockfish display when navigating with buttons too
            if "show_stockfish" in st.session_state:
                st.session_state.show_stockfish = False

    with col1:
        st.button(
            "← Previous",
            on_click=prev_position,
            key="prev_button",
            disabled=disable_prev,
            use_container_width=True
        )
    with col2:
        st.button(
            "Next →",
            on_click=next_position,
            key="next_button",
            disabled=disable_next,
            use_container_width=True
        )

    st.sidebar.divider()

    # --- Position Selection Dropdown ---
    if not position_ids:
        st.sidebar.info("No positions available for this Cohort Pair.")
        return None # Explicitly return None if no positions

    # Ensure position_index is valid before using it for the selectbox default
    clamp_position_index(position_ids) # Ensures index is within [0, num_positions-1]

    # Let user directly select from the position IDs using display index
    position_display_options = range(num_positions)
    # Format function shows the actual PositionIdx from the data
    def format_position_option(display_index):
         # Handle potential index out of bounds if position_ids is modified unexpectedly
         try:
             actual_position_id = position_ids[display_index]
             return f"Position {actual_position_id} (Index {display_index})"
         except IndexError:
             return f"Invalid Index {display_index}"

    selected_display_index = st.sidebar.selectbox(
        "Select Position:",
        options=position_display_options,
        index=st.session_state["position_index"],
        format_func=format_position_option,
        key="position_selector", # Add key
        label_visibility="collapsed" # Hide label, rely on title/divider
    )

    # Update session state based on selectbox choice *before* returning
    # update_position_index handles resetting stockfish display
    update_position_index(selected_display_index)

    # Return the actual position ID corresponding to the selected display index
    # Safely access position_ids using the validated index from session state
    try:
        return position_ids[st.session_state["position_index"]]
    except IndexError:
         st.error("Error retrieving selected position ID.")
         return None # Return None on error