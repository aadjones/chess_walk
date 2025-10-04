# sidebar.py
"""Handles the creation and logic of the Streamlit sidebar."""

import streamlit as st


def create_cohort_pair_selector(unique_pairs):
    """Create the selectbox for choosing a Cohort Pair.

    Changing cohort automatically resets to position 1 of that cohort.
    """
    st.sidebar.subheader("Select Cohort Pair")
    if not unique_pairs:
        st.sidebar.warning("No Cohort Pairs found in data.")
        return None

    current_selection = st.session_state.get("cohort_filter", "1400-1800")
    if current_selection not in unique_pairs:
        current_selection = unique_pairs[0]

    try:
        default_index = unique_pairs.index(current_selection)
    except ValueError:
        default_index = 0

    def format_cohort_pair(pair):
        return pair.replace("-", " vs ")

    new_cohort_pair = st.sidebar.selectbox(
        "Cohort Pair:",
        unique_pairs,
        index=default_index,
        format_func=format_cohort_pair,
        key="cohort_pair_selector",
        label_visibility="collapsed",
    )

    # If cohort changed, reset to position 0 and hide stockfish
    if new_cohort_pair != current_selection:
        st.session_state["cohort_filter"] = new_cohort_pair
        st.session_state["position_index"] = 0
        if "show_stockfish" in st.session_state:
            st.session_state.show_stockfish = False
        st.rerun()

    st.session_state["cohort_filter"] = new_cohort_pair
    return new_cohort_pair


def create_position_controls(position_ids):
    """Create sidebar controls for position navigation within current cohort.

    Args:
        position_ids: List of position IDs in the current cohort (sorted)

    Returns:
        The current position ID
    """
    st.sidebar.divider()
    st.sidebar.title("Position Controls")

    if not position_ids:
        st.sidebar.info("No positions in this cohort.")
        return None

    num_positions = len(position_ids)
    current_index = st.session_state.get("position_index", 0)

    # Clamp index to valid range
    current_index = max(0, min(current_index, num_positions - 1))
    st.session_state["position_index"] = current_index

    # --- Position Counter ---
    st.sidebar.caption(f"Position {current_index + 1} of {num_positions}")

    # --- Previous/Next Buttons ---
    col1, col2 = st.sidebar.columns(2)

    with col1:
        if st.button("← Previous", key="prev_button", disabled=(current_index <= 0), width="stretch"):
            st.session_state["position_index"] -= 1
            if "show_stockfish" in st.session_state:
                st.session_state.show_stockfish = False
            st.rerun()

    with col2:
        if st.button("Next →", key="next_button", disabled=(current_index >= num_positions - 1), width="stretch"):
            st.session_state["position_index"] += 1
            if "show_stockfish" in st.session_state:
                st.session_state.show_stockfish = False
            st.rerun()

    # Helpful reminder
    st.sidebar.caption("💡 Change cohort above to see different positions")

    return position_ids[current_index]
