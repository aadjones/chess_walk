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

    # Use all_position_ids for global dropdown if available, otherwise fall back to cohort-local
    dropdown_position_ids = all_position_ids if all_position_ids is not None else position_ids
    position_display_options = range(len(dropdown_position_ids))
    
    # Format function shows the actual PositionIdx from the data
    def format_position_option(display_index):
         # Handle potential index out of bounds if position_ids is modified unexpectedly
         try:
             actual_position_id = dropdown_position_ids[display_index]
             return f"Position {actual_position_id}"
         except IndexError:
             return f"Invalid Position"

    # Show global context in dropdown label
    global_label = f"Jump to any position (1-{total_positions})" if total_positions else "Select Position:"
    
    # For global dropdown, find the index of the current position
    current_position_id = position_ids[st.session_state.get("position_index", 0)] if position_ids else None
    try:
        dropdown_default_index = dropdown_position_ids.index(current_position_id) if current_position_id in dropdown_position_ids else 0
    except (ValueError, IndexError):
        dropdown_default_index = 0
    
    selected_display_index = st.sidebar.selectbox(
        global_label,
        options=position_display_options,
        index=dropdown_default_index,
        format_func=format_position_option,
        key="position_selector", # Add key
        label_visibility="visible"  # Show the label to explain global context
    )

    # Get the selected position ID from the dropdown
    try:
        selected_position_id = dropdown_position_ids[selected_display_index]
    except IndexError:
        st.error("Error retrieving selected position ID.")
        return None

    # If using global dropdown and user selected a position outside current cohort,
    # we need to return the selected position ID directly without updating local session state
    if all_position_ids is not None and selected_position_id not in position_ids:
        # User selected a position from a different cohort - return it directly
        return selected_position_id
    else:
        # User selected a position within current cohort - use normal session state logic
        # Find the local index of the selected position
        try:
            local_index = position_ids.index(selected_position_id)
            update_position_index(local_index)
            return selected_position_id
        except ValueError:
            # This shouldn't happen, but handle gracefully
            update_position_index(selected_display_index)
            return position_ids[st.session_state["position_index"]] if position_ids else None