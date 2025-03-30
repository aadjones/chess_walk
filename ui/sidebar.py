# sidebar.py
"""Handles the creation and logic of the Streamlit sidebar."""

import streamlit as st
from session_state_utils import clamp_puzzle_index, update_cohort_pair, update_puzzle_index
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


def create_puzzle_controls(puzzle_ids):
    """Create sidebar controls for puzzle navigation and return the chosen puzzle ID."""
    st.sidebar.title("Puzzle Controls")

    num_puzzles = len(puzzle_ids)
    # Ensure index exists and is valid before accessing
    current_index = st.session_state.get("puzzle_index", 0)
    if num_puzzles > 0:
        current_index = max(0, min(current_index, num_puzzles - 1))
    else:
        current_index = 0


    # --- Navigation Buttons ---
    st.sidebar.caption(f"Puzzle {current_index + 1} of {num_puzzles}" if num_puzzles > 0 else "No puzzles")
    col1, col2 = st.sidebar.columns(2)

    # Disable buttons appropriately
    disable_prev = (current_index <= 0)
    disable_next = (current_index >= num_puzzles - 1)

    def prev_puzzle():
        if st.session_state["puzzle_index"] > 0:
            st.session_state["puzzle_index"] -= 1
            # Need to reset Stockfish display when navigating with buttons too
            if "show_stockfish" in st.session_state:
                st.session_state.show_stockfish = False

    def next_puzzle():
        if st.session_state["puzzle_index"] < num_puzzles - 1:
            st.session_state["puzzle_index"] += 1
            # Need to reset Stockfish display when navigating with buttons too
            if "show_stockfish" in st.session_state:
                st.session_state.show_stockfish = False

    with col1:
        st.button(
            "← Previous",
            on_click=prev_puzzle,
            key="prev_button",
            disabled=disable_prev,
            use_container_width=True
        )
    with col2:
        st.button(
            "Next →",
            on_click=next_puzzle,
            key="next_button",
            disabled=disable_next,
            use_container_width=True
        )

    st.sidebar.divider()

    # --- Puzzle Selection Dropdown ---
    if not puzzle_ids:
        st.sidebar.info("No puzzles available for this Cohort Pair.")
        return None # Explicitly return None if no puzzles

    # Ensure puzzle_index is valid before using it for the selectbox default
    clamp_puzzle_index(puzzle_ids) # Ensures index is within [0, num_puzzles-1]

    # Let user directly select from the puzzle IDs using display index
    puzzle_display_options = range(num_puzzles)
    # Format function shows the actual PuzzleIdx from the data
    def format_puzzle_option(display_index):
         # Handle potential index out of bounds if puzzle_ids is modified unexpectedly
         try:
             actual_puzzle_id = puzzle_ids[display_index]
             return f"Puzzle {actual_puzzle_id} (Index {display_index})"
         except IndexError:
             return f"Invalid Index {display_index}"

    selected_display_index = st.sidebar.selectbox(
        "Select Puzzle:",
        options=puzzle_display_options,
        index=st.session_state["puzzle_index"],
        format_func=format_puzzle_option,
        key="puzzle_selector", # Add key
        label_visibility="collapsed" # Hide label, rely on title/divider
    )

    # Update session state based on selectbox choice *before* returning
    # update_puzzle_index handles resetting stockfish display
    update_puzzle_index(selected_display_index)

    # Return the actual puzzle ID corresponding to the selected display index
    # Safely access puzzle_ids using the validated index from session state
    try:
        return puzzle_ids[st.session_state["puzzle_index"]]
    except IndexError:
         st.error("Error retrieving selected puzzle ID.")
         return None # Return None on error