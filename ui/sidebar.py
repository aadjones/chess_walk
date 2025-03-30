# sidebar.py
"""Handles the creation and logic of the Streamlit sidebar."""

import streamlit as st
from session_state_utils import clamp_puzzle_index, update_cohort_pair, update_puzzle_index

def create_cohort_pair_selector(unique_pairs):
    """Create the selectbox for choosing a Cohort Pair."""
    if not unique_pairs:
        st.sidebar.warning("No Cohort Pairs found in data.")
        return None

    # Determine default index safely
    current_selection = st.session_state.get("selected_cohort_pair", unique_pairs[0])
    try:
        default_index = unique_pairs.index(current_selection)
    except ValueError:
        default_index = 0 # Default to first item if current selection isn't valid

    new_cohort_pair = st.sidebar.selectbox(
        "Select Cohort Pair",
        unique_pairs,
        index=default_index,
        key="cohort_pair_selector" # Add key for stability
    )
    update_cohort_pair(new_cohort_pair)
    return st.session_state["selected_cohort_pair"]


def create_puzzle_controls(puzzle_ids):
    """Create sidebar controls for puzzle navigation and return the chosen puzzle ID."""
    st.sidebar.title("Puzzle Controls")

    num_puzzles = len(puzzle_ids)
    current_index = st.session_state.get("puzzle_index", 0)

    # --- Navigation Buttons ---
    def prev_puzzle():
        if st.session_state["puzzle_index"] > 0:
            st.session_state["puzzle_index"] -= 1

    def next_puzzle():
        # Use num_puzzles directly for clarity
        if st.session_state["puzzle_index"] < num_puzzles - 1:
            st.session_state["puzzle_index"] += 1

    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.button(
            "← Previous",
            on_click=prev_puzzle,
            key="prev_button",
            disabled=current_index <= 0 # Disable if at the start
        )
    with col2:
        st.button(
            "Next →",
            on_click=next_puzzle,
            key="next_button",
            disabled=current_index >= num_puzzles - 1 # Disable if at the end
        )

    # --- Puzzle Selection ---
    if not puzzle_ids:
        st.sidebar.info("No puzzles available for this Cohort Pair.")
        return None

    # Ensure puzzle_index is valid before using it
    clamp_puzzle_index(puzzle_ids)

    # Let user directly select from the puzzle IDs using display index
    puzzle_display_options = range(num_puzzles)
    selected_display_index = st.sidebar.selectbox(
        "Select Puzzle",
        options=puzzle_display_options,
        index=st.session_state["puzzle_index"],
        # Display puzzle ID + 1 for 1-based indexing view
        format_func=lambda i: f"Puzzle {puzzle_ids[i]} (Index {i})",
        key="puzzle_selector" # Add key
    )

    # Update session state based on selectbox choice *before* returning
    update_puzzle_index(selected_display_index)

    # Return the actual puzzle ID corresponding to the selected display index
    return puzzle_ids[st.session_state["puzzle_index"]]