import os
import sys

import chess
import chess.svg
import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.chess_utils import generate_board_svg_with_arrows, uci_to_san

# Use wide layout for better use of space
st.set_page_config(layout="wide")


def load_puzzle_data():
    """Load and group puzzle data from CSV."""
    puzzles_df = pd.read_csv("output/puzzles.csv", index_col=["Cohort", "Row", "PuzzleIdx"])
    puzzle_groups = puzzles_df.groupby("PuzzleIdx")
    puzzle_ids = sorted(list(puzzle_groups.groups.keys()))
    return puzzles_df, puzzle_groups, puzzle_ids


def initialize_session_state(puzzle_ids):
    """Initialize session state with puzzle data and index."""
    if "puzzle_ids" not in st.session_state:
        st.session_state["puzzle_ids"] = puzzle_ids
    if "puzzle_index" not in st.session_state:
        st.session_state["puzzle_index"] = 0


def create_sidebar_controls(puzzle_ids):
    """Create sidebar controls for puzzle navigation."""
    st.sidebar.title("Puzzle Controls")

    def prev_puzzle():
        if st.session_state.puzzle_index > 0:
            st.session_state.puzzle_index -= 1

    def next_puzzle():
        if st.session_state.puzzle_index < len(st.session_state.puzzle_ids) - 1:
            st.session_state.puzzle_index += 1

    # Create two columns for horizontal button layout
    col1, col2 = st.sidebar.columns(2)

    with col1:
        st.button("← Previous", on_click=prev_puzzle, key="prev_button")
    with col2:
        st.button("Next →", on_click=next_puzzle, key="next_button")

    selected_index = st.sidebar.selectbox(
        "Select Puzzle",
        options=range(len(st.session_state.puzzle_ids)),
        index=st.session_state.puzzle_index,
        format_func=lambda i: f"Puzzle {st.session_state.puzzle_ids[i] + 1}",
    )
    st.session_state.puzzle_index = selected_index
    return st.session_state.puzzle_ids[st.session_state.puzzle_index]


def process_puzzle_data(puzzle_groups, current_puzzle_id):
    """Retrieve and process data for the selected puzzle."""
    puzzle = puzzle_groups.get_group(current_puzzle_id).copy()
    return puzzle


def prepare_board_data(puzzle):
    """Prepare chessboard data including FEN and top moves for arrows."""
    fen = puzzle["FEN"].iloc[0]
    board = chess.Board(fen)

    base_data = puzzle[puzzle.index.get_level_values("Cohort") == "base"].copy()
    target_data = puzzle[puzzle.index.get_level_values("Cohort") == "target"].copy()
    base_data.sort_values("Freq", ascending=False, inplace=True)
    target_data.sort_values("Freq", ascending=False, inplace=True)
    base_top_uci = base_data["Move"].iloc[0] if not base_data.empty else None
    target_top_uci = target_data["Move"].iloc[0] if not target_data.empty else None

    svg_board = generate_board_svg_with_arrows(fen=fen, base_uci=base_top_uci, target_uci=target_top_uci, size=500)
    return board, svg_board, base_data, target_data


def convert_moves_to_san(base_data, target_data, fen):
    """Convert UCI moves to SAN notation for display."""
    if "Move" in base_data.columns:
        base_data.loc[:, "Move"] = base_data["Move"].apply(lambda m: uci_to_san(fen, m))
    if "Move" in target_data.columns:
        target_data.loc[:, "Move"] = target_data["Move"].apply(lambda m: uci_to_san(fen, m))
    return base_data, target_data


def cleanup_data(base_data, target_data):
    """Clean up DataFrames by removing unnecessary columns and formatting data."""
    for df in (base_data, target_data):
        for col in ["Cohort", "PuzzleIdx"]:
            if col in df.columns:
                df.drop(columns=col, inplace=True)
        if "Freq" in df.columns:
            df.loc[:, "Freq"] = df["Freq"] * 100
        if "Games" in df.columns:
            df.loc[:, "Games"] = df["Games"].astype(int)
        df.reset_index(drop=True, inplace=True)
        df.index = df.index + 1

    base_data.sort_values("Freq", ascending=False, inplace=True)
    target_data.sort_values("Freq", ascending=False, inplace=True)
    return base_data, target_data


def infer_ratings_and_format_wdl(base_data, target_data):
    """Infer ratings and combine W/D/L percentages into a single column."""
    base_rating = base_data["Rating"].iloc[0] if "Rating" in base_data.columns else "Base"
    target_rating = target_data["Rating"].iloc[0] if "Rating" in target_data.columns else "Target"

    def format_wdl(row):
        return f"{row['White %']:.1f}% / {row['Draw %']:.1f}% / {row['Black %']:.1f}%"

    base_data["W/D/L"] = base_data.apply(format_wdl, axis=1)
    target_data["W/D/L"] = target_data.apply(format_wdl, axis=1)
    for col in ["White %", "Draw %", "Black %"]:
        for df in (base_data, target_data):
            if col in df.columns:
                df.drop(columns=col, inplace=True)

    return base_rating, target_rating, base_data, target_data


def prepare_display_data(base_data, target_data):
    """Prepare DataFrames for display with selected columns and formatted frequencies."""
    display_cols = ["Move", "Games", "W/D/L", "Freq"]
    base_display = base_data[[c for c in display_cols if c in base_data.columns]].copy()
    target_display = target_data[[c for c in display_cols if c in target_data.columns]].copy()

    # Format Freq as percentage strings and assign directly to avoid FutureWarning
    if "Freq" in base_display.columns:
        base_display["Freq"] = base_data["Freq"].apply(lambda x: f"{float(x):.1f}%")
        base_display["Freq"] = base_display["Freq"].astype("object")  # Ensure string dtype
    if "Freq" in target_display.columns:
        target_display["Freq"] = target_data["Freq"].apply(lambda x: f"{float(x):.1f}%")
        target_display["Freq"] = target_display["Freq"].astype("object")  # Ensure string dtype

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
    # Load and initialize data
    puzzles_df, puzzle_groups, puzzle_ids = load_puzzle_data()
    initialize_session_state(puzzle_ids)

    # Handle user input
    current_puzzle_id = create_sidebar_controls(puzzle_ids)

    # Process puzzle data
    puzzle = process_puzzle_data(puzzle_groups, current_puzzle_id)

    # Prepare board and move data
    board, svg_board, base_data, target_data = prepare_board_data(puzzle)

    # Convert and clean data
    base_data, target_data = convert_moves_to_san(base_data, target_data, puzzle["FEN"].iloc[0])
    base_data, target_data = cleanup_data(base_data, target_data)

    # Format ratings and W/D/L
    base_rating, target_rating, base_data, target_data = infer_ratings_and_format_wdl(base_data, target_data)

    # Prepare for display
    base_display, target_display = prepare_display_data(base_data, target_data)

    # Render layout
    layout_display(puzzle["FEN"].iloc[0], svg_board, base_rating, target_rating, base_display, target_display)


if __name__ == "__main__":
    main()
