import os
import sys

import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.chess_utils import generate_board_svg_with_arrows, uci_to_san

# Use wide layout for better use of space
st.set_page_config(layout="wide")


def load_puzzle_data():
    """Load the entire puzzles CSV as a DataFrame (unfiltered)."""
    # Don't set index_col here; keep all columns.
    puzzles_df = pd.read_csv("output/puzzles.csv")
    return puzzles_df


def initialize_session_state():
    """Initialize session state variables if they don't exist."""
    if "puzzle_index" not in st.session_state:
        st.session_state["puzzle_index"] = 0
    # We'll handle "selected_cohort_pair" in main().


def clamp_puzzle_index(puzzle_ids):
    """
    Ensure puzzle_index is in [0, len(puzzle_ids)-1].
    If puzzle_ids is empty, puzzle_index stays 0 (we'll handle empty set).
    """
    if len(puzzle_ids) == 0:
        st.session_state["puzzle_index"] = 0
    else:
        st.session_state["puzzle_index"] = max(0, min(st.session_state["puzzle_index"], len(puzzle_ids) - 1))


def create_sidebar_controls(puzzle_ids):
    """Create sidebar controls for puzzle navigation and return the chosen puzzle ID."""
    st.sidebar.title("Puzzle Controls")

    def prev_puzzle():
        if st.session_state["puzzle_index"] > 0:
            st.session_state["puzzle_index"] -= 1

    def next_puzzle():
        if st.session_state["puzzle_index"] < len(puzzle_ids) - 1:
            st.session_state["puzzle_index"] += 1

    # Create two columns for horizontal button layout
    col1, col2 = st.sidebar.columns(2)

    with col1:
        st.button("← Previous", on_click=prev_puzzle, key="prev_button")
    with col2:
        st.button("Next →", on_click=next_puzzle, key="next_button")

    # If puzzle_ids is empty, there's nothing to select
    if not puzzle_ids:
        st.sidebar.info("No puzzles available for this Cohort Pair.")
        return None

    # If puzzle_ids has items, clamp puzzle_index to a valid range
    clamp_puzzle_index(puzzle_ids)

    # Let user directly select from the puzzle IDs
    # puzzle_ids might look like [100, 101, 102, ...]
    # We map them to enumerated indices for the selectbox
    puzzle_index_options = range(len(puzzle_ids))
    selected_index = st.sidebar.selectbox(
        "Select Puzzle",
        options=puzzle_index_options,
        index=st.session_state["puzzle_index"],
        format_func=lambda i: f"Puzzle {puzzle_ids[i] + 1}",  # +1 because puzzle_ids are 1-indexed in the frontend
    )
    st.session_state["puzzle_index"] = selected_index

    # Return the actual puzzle ID from puzzle_ids
    return puzzle_ids[selected_index]


def process_puzzle_data(puzzle_groups, current_puzzle_id):
    """Retrieve and process data for the selected puzzle."""
    if current_puzzle_id is None:
        return None
    # puzzle_groups.get_group(...) can raise KeyError if the group doesn't exist
    # but we should only call this if current_puzzle_id is definitely valid
    puzzle = puzzle_groups.get_group(current_puzzle_id).copy()
    return puzzle


def prepare_board_data(puzzle):
    """Prepare chessboard data including FEN and top moves for arrows."""
    import chess

    fen = puzzle["FEN"].iloc[0]
    board = chess.Board(fen)

    # We'll assume Cohort has "base"/"target" or something similar
    base_data = puzzle[puzzle["Cohort"] == "base"].copy()
    target_data = puzzle[puzzle["Cohort"] == "target"].copy()
    base_data.sort_values("Freq", ascending=False, inplace=True)
    target_data.sort_values("Freq", ascending=False, inplace=True)

    base_top_uci = base_data["Move"].iloc[0] if not base_data.empty else None
    target_top_uci = target_data["Move"].iloc[0] if not target_data.empty else None

    svg_board = generate_board_svg_with_arrows(fen=fen, base_uci=base_top_uci, target_uci=target_top_uci, size=500)
    return board, svg_board, base_data, target_data


def convert_moves_to_san(base_data, target_data, fen):
    """Convert UCI moves to SAN notation for display."""
    if base_data is not None and not base_data.empty:
        base_data.loc[:, "Move"] = base_data["Move"].apply(lambda m: uci_to_san(fen, m))
    if target_data is not None and not target_data.empty:
        target_data.loc[:, "Move"] = target_data["Move"].apply(lambda m: uci_to_san(fen, m))
    return base_data, target_data


def cleanup_data(base_data, target_data):
    """Clean up DataFrames by removing unnecessary columns and formatting data."""
    for df in (base_data, target_data):
        if df is None or df.empty:
            continue
        for col in ["Cohort", "PuzzleIdx", "CohortPair"]:
            if col in df.columns:
                df.drop(columns=col, inplace=True)
        if "Freq" in df.columns:
            df.loc[:, "Freq"] = df["Freq"] * 100
        if "Games" in df.columns:
            df.loc[:, "Games"] = df["Games"].astype(int)
        df.reset_index(drop=True, inplace=True)
        df.index = df.index + 1

    if base_data is not None and not base_data.empty:
        base_data.sort_values("Freq", ascending=False, inplace=True)
    if target_data is not None and not target_data.empty:
        target_data.sort_values("Freq", ascending=False, inplace=True)
    return base_data, target_data


def infer_ratings_and_format_wdl(base_data, target_data):
    """Infer ratings and combine W/D/L percentages into a single column."""
    base_rating = "Base"
    target_rating = "Target"
    if base_data is not None and not base_data.empty and "Rating" in base_data.columns:
        base_rating = base_data["Rating"].iloc[0]
    if target_data is not None and not target_data.empty and "Rating" in target_data.columns:
        target_rating = target_data["Rating"].iloc[0]

    def format_wdl(row):
        return f"{row['White %']:.1f}% / {row['Draw %']:.1f}% / {row['Black %']:.1f}%"

    for df in (base_data, target_data):
        if df is not None and not df.empty:
            df["W/D/L"] = df.apply(format_wdl, axis=1)
            for col in ["White %", "Draw %", "Black %"]:
                if col in df.columns:
                    df.drop(columns=col, inplace=True)

    return base_rating, target_rating, base_data, target_data


def prepare_display_data(base_data, target_data):
    """Prepare DataFrames for display with selected columns and formatted frequencies."""
    display_cols = ["Move", "Games", "W/D/L", "Freq"]

    def format_freq(df):
        if df is not None and not df.empty and "Freq" in df.columns:
            df["Freq"] = df["Freq"].apply(lambda x: f"{float(x):.1f}%")
            df["Freq"] = df["Freq"].astype("object")  # ensure string dtype
        return df

    base_data = format_freq(base_data)
    target_data = format_freq(target_data)

    if base_data is not None and not base_data.empty:
        base_display = base_data[[c for c in display_cols if c in base_data.columns]].copy()
    else:
        base_display = pd.DataFrame(columns=display_cols)

    if target_data is not None and not target_data.empty:
        target_display = target_data[[c for c in display_cols if c in target_data.columns]].copy()
    else:
        target_display = pd.DataFrame(columns=display_cols)

    return base_display, target_display


def layout_display(fen, svg_board, base_rating, target_rating, base_display, target_display):
    """Lay out the board and tables in a three-column format."""
    left_col, mid_col, right_col = st.columns([3, 4, 4])

    with left_col:
        st.markdown("### Board Position")
        st.write(f"**FEN**: `{fen}`")
        st.image(svg_board, use_container_width=True)

    with mid_col:
        st.markdown(f"### Base Cohort ({base_rating})")
        st.dataframe(base_display, use_container_width=True)

    with right_col:
        st.markdown(f"### Target Cohort ({target_rating})")
        st.dataframe(target_display, use_container_width=True)


def main():
    """Main function to orchestrate the app workflow."""
    # Initialize session state
    initialize_session_state()

    # Load the full puzzle data
    puzzles_df = load_puzzle_data()

    # Get unique CohortPair values
    unique_pairs = sorted(puzzles_df["CohortPair"].unique())

    # If there's no data at all
    if not unique_pairs:
        st.warning("No CohortPair data found in CSV.")
        st.stop()

    # Track old and new CohortPair so we can reset puzzle_index if changed
    old_cohort_pair = st.session_state.get("selected_cohort_pair", unique_pairs[0])

    new_cohort_pair = st.sidebar.selectbox(
        "Select Cohort Pair",
        unique_pairs,
        index=unique_pairs.index(old_cohort_pair) if old_cohort_pair in unique_pairs else 0,
    )

    # If the user picked a different pair, reset puzzle_index
    if new_cohort_pair != old_cohort_pair:
        st.session_state["selected_cohort_pair"] = new_cohort_pair
        st.session_state["puzzle_index"] = 0
    else:
        # Otherwise keep the old one in session state
        st.session_state["selected_cohort_pair"] = old_cohort_pair

    # Filter the data to only the chosen CohortPair
    filtered_df = puzzles_df[puzzles_df["CohortPair"] == st.session_state["selected_cohort_pair"]]

    # Edge case: If there's no data for this pair
    if filtered_df.empty:
        st.warning("No data found for this CohortPair!")
        st.stop()

    # Group by PuzzleIdx for the chosen pair
    puzzle_groups = filtered_df.groupby("PuzzleIdx")
    puzzle_ids = sorted(list(puzzle_groups.groups.keys()))

    # If puzzle_ids is empty for some reason, stop
    if not puzzle_ids:
        st.warning("No puzzles available after filtering!")
        st.stop()

    # Create puzzle controls & get the current puzzle ID
    current_puzzle_id = create_sidebar_controls(puzzle_ids)
    if current_puzzle_id is None:
        st.stop()

    # Process puzzle data
    puzzle = process_puzzle_data(puzzle_groups, current_puzzle_id)
    if puzzle is None or puzzle.empty:
        st.warning("No puzzle data found for the current puzzle ID!")
        st.stop()

    # Prepare board and move data
    board, svg_board, base_data, target_data = prepare_board_data(puzzle)

    # Convert moves to SAN
    base_data, target_data = convert_moves_to_san(base_data, target_data, puzzle["FEN"].iloc[0])

    # Clean up DataFrames
    base_data, target_data = cleanup_data(base_data, target_data)

    # Format ratings and W/D/L
    base_rating, target_rating, base_data, target_data = infer_ratings_and_format_wdl(base_data, target_data)

    # Prepare for display
    base_display, target_display = prepare_display_data(base_data, target_data)

    # Render layout
    layout_display(puzzle["FEN"].iloc[0], svg_board, base_rating, target_rating, base_display, target_display)


if __name__ == "__main__":
    main()
