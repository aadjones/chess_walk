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

    # Format cohort pairs for display (replace - with vs)
    def format_cohort_pair(pair):
        return pair.replace("-", " vs ")

    new_cohort_pair = st.sidebar.selectbox(
        "Cohort Pair:", # Shorten label
        unique_pairs,
        index=default_index,
        format_func=format_cohort_pair,  # Format display text
        key="cohort_pair_selector", # Add key for stability
        label_visibility="collapsed" # Hide label if subheader is enough
    )
    # update_cohort_pair handles session state logic
    update_cohort_pair(new_cohort_pair)
    return st.session_state["selected_cohort_pair"]


def create_position_controls(position_ids, total_positions=None, all_position_ids=None):
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

    # Super simple approach: just use number input
    current_pos_index = st.session_state.get("position_index", 0)
    current_pos_id = position_ids[current_pos_index] if position_ids and current_pos_index < len(position_ids) else 1
    
    if all_position_ids is not None:
        min_pos = min(all_position_ids)
        max_pos = max(all_position_ids)
        label = f"Jump to position ({min_pos}-{max_pos}):"
    else:
        min_pos = min(position_ids) if position_ids else 1
        max_pos = max(position_ids) if position_ids else 1
        label = "Select position:"
    
    selected_position_id = st.sidebar.number_input(
        label,
        min_value=min_pos,
        max_value=max_pos,
        value=current_pos_id,
        step=1,
        key="position_number_input"
    )

    # Just return the selected position ID - let the main app handle everything
    return selected_position_id