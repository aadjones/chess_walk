# puzzle_logic.py
"""Core logic for processing selected puzzle data."""

import chess
import pandas as pd
import streamlit as st
# Assuming chess_utils exists in src/ relative to the location of THIS file
# Adjust path if necessary based on your actual project structure
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.chess_utils import generate_board_svg_with_arrows, uci_to_san
from config import COL_PUZZLE_IDX, COL_FEN, COL_MOVE, COL_COHORT, COL_FREQ, BASE_COHORT_ID, TARGET_COHORT_ID

def get_puzzle_data(puzzle_groups, current_puzzle_id):
    """Retrieve and process data for the selected puzzle."""
    if current_puzzle_id is None or puzzle_groups is None:
        return None
    try:
        # puzzle_groups.get_group(...) can raise KeyError if the group doesn't exist
        puzzle_df = puzzle_groups.get_group(current_puzzle_id).copy()
        if puzzle_df.empty:
             st.warning(f"No data found for Puzzle ID {current_puzzle_id}.")
             return None
        return puzzle_df
    except KeyError:
        st.error(f"Internal Error: Puzzle ID {current_puzzle_id} not found in groups.")
        return None
    except Exception as e:
        st.error(f"An error occurred retrieving puzzle data: {e}")
        return None


def prepare_board_data(puzzle_df):
    """Prepare chessboard data including FEN and top moves for arrows."""
    if puzzle_df is None or puzzle_df.empty:
        st.error("Cannot prepare board data: Puzzle data is missing.")
        return None, None, pd.DataFrame(), pd.DataFrame() # Return empty dfs

    if COL_FEN not in puzzle_df.columns:
        st.error(f"'{COL_FEN}' column missing in puzzle data.")
        return None, None, pd.DataFrame(), pd.DataFrame()

    fen = puzzle_df[COL_FEN].iloc[0]
    try:
        board = chess.Board(fen)
    except ValueError:
        st.error(f"Invalid FEN string encountered: {fen}")
        return None, None, pd.DataFrame(), pd.DataFrame()

    # Separate data for base and target cohorts
    base_data = puzzle_df[puzzle_df[COL_COHORT] == BASE_COHORT_ID].copy()
    target_data = puzzle_df[puzzle_df[COL_COHORT] == TARGET_COHORT_ID].copy()

    # Sort by frequency to find top moves
    base_data.sort_values(COL_FREQ, ascending=False, inplace=True)
    target_data.sort_values(COL_FREQ, ascending=False, inplace=True)

    base_top_uci = base_data[COL_MOVE].iloc[0] if not base_data.empty else None
    target_top_uci = target_data[COL_MOVE].iloc[0] if not target_data.empty else None

    # Generate SVG
    try:
        svg_board = generate_board_svg_with_arrows(
            fen=fen,
            base_uci=base_top_uci,
            target_uci=target_top_uci,
            size=500 # Consider making size configurable
        )
    except Exception as e: # Catch potential errors in SVG generation
        st.error(f"Error generating board SVG: {e}")
        svg_board = None # Handle gracefully

    return board, svg_board, base_data, target_data


def convert_moves_to_san(base_data, target_data, fen):
    """Convert UCI moves to SAN notation for display."""
    if fen is None:
        st.error("Cannot convert moves to SAN: FEN string is missing.")
        return base_data, target_data # Return original data

    def _safe_uci_to_san(move_uci):
        if pd.isna(move_uci): return None # Handle missing moves
        try:
            return uci_to_san(fen, move_uci)
        except Exception as e:
            # Log or warn about conversion errors for specific moves
            st.warning(f"Could not convert UCI '{move_uci}' to SAN for FEN '{fen}': {e}")
            return move_uci # Return original UCI on error

    if base_data is not None and not base_data.empty and COL_MOVE in base_data.columns:
        base_data[COL_MOVE] = base_data[COL_MOVE].apply(_safe_uci_to_san)
    if target_data is not None and not target_data.empty and COL_MOVE in target_data.columns:
        target_data[COL_MOVE] = target_data[COL_MOVE].apply(_safe_uci_to_san)

    return base_data, target_data