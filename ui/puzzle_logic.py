# puzzle_logic.py
"""Core logic for processing selected position data, including Stockfish analysis."""

import chess
import pandas as pd
import streamlit as st
import os
import sys
from stockfish import Stockfish  # Import Stockfish library
import math  # For checking NaN/inf in evaluations

# Path setup for src/chess_utils (adjust if your structure differs)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from src.chess_utils import generate_board_svg_with_arrows, uci_to_san
except ImportError:
    st.error(
        "Could not import `chess_utils`. Please ensure `src/chess_utils.py` exists relative to the app's execution directory or adjust `sys.path`."
    )

    def generate_board_svg_with_arrows(fen, base_uci, target_uci, size):
        return None

    def uci_to_san(fen, uci):
        return uci  # Fallback


# Import the single settings instance from config.py
from config import settings


# --- Data Retrieval ---
def get_position_data(position_groups, current_position_id):
    """Get position data for the selected position ID."""
    if current_position_id is None or position_groups is None:
        return None
    try:
        position_df = position_groups.get_group(current_position_id).copy()
        if position_df.empty:
            st.warning(f"No data found for Position ID {current_position_id}.")
            return None
        return position_df
    except KeyError:
        st.error(f"Internal Error: Position ID {current_position_id} not found in groups.")
        return None
    except Exception as e:
        st.error(f"An error occurred retrieving position data: {e}")
        return None


# --- Board and Move Preparation ---
def prepare_board_data(position_df):
    """Prepare board data for the selected position."""
    if position_df is None or position_df.empty:
        return None, None, pd.DataFrame(), pd.DataFrame(), None, None
    if settings.col_fen not in position_df.columns:
        return None, None, pd.DataFrame(), pd.DataFrame(), None, None
    fen = position_df[settings.col_fen].iloc[0]
    try:
        board = chess.Board(fen)
    except ValueError:
        return None, None, pd.DataFrame(), pd.DataFrame(), None, None
    base_data = position_df[position_df[settings.col_cohort] == settings.base_cohort_id].copy()
    target_data = position_df[position_df[settings.col_cohort] == settings.target_cohort_id].copy()
    if settings.col_freq in base_data.columns:
        base_data.sort_values(settings.col_freq, ascending=False, inplace=True)
    if settings.col_freq in target_data.columns:
        target_data.sort_values(settings.col_freq, ascending=False, inplace=True)
    base_top_uci = None
    if not base_data.empty and settings.col_move in base_data.columns:
        base_top_uci = base_data[settings.col_move].iloc[0]
    target_top_uci = None
    if not target_data.empty and settings.col_move in target_data.columns:
        target_top_uci = target_data[settings.col_move].iloc[0]
    svg_board = None
    try:
        if "generate_board_svg_with_arrows" in globals() and callable(generate_board_svg_with_arrows):
            svg_board = generate_board_svg_with_arrows(
                fen=fen, base_uci=base_top_uci, target_uci=target_top_uci, size=500
            )
        else:
            st.warning("SVG generation function not available.")
    except Exception as e:
        st.error(f"Error generating board SVG: {e}")
    return board, svg_board, base_data, target_data, base_top_uci, target_top_uci


# --- Move Conversion (keep convert_moves_to_san as is) ---
def convert_moves_to_san(base_data, target_data, fen):
    # ... (function content unchanged) ...
    if fen is None:
        st.error("Cannot convert moves to SAN: FEN string is missing.")
        return base_data, target_data
    if "uci_to_san" not in globals() or not callable(uci_to_san):
        st.warning("uci_to_san function not available...")
        return base_data, target_data

    def _safe_uci_to_san(move_uci):
        if pd.isna(move_uci):
            return None
        try:
            return uci_to_san(fen, move_uci)
        except Exception as e:
            st.warning(f"Could not convert UCI '{move_uci}': {e}")
            return move_uci

    move_col = settings.col_move
    if base_data is not None and not base_data.empty and move_col in base_data.columns:
        base_data.loc[:, move_col] = base_data[move_col].apply(_safe_uci_to_san)
    if target_data is not None and not target_data.empty and move_col in target_data.columns:
        target_data.loc[:, move_col] = target_data[move_col].apply(_safe_uci_to_san)
    return base_data, target_data


# --- Stockfish Analysis (Revised: Base and Target Only) ---


def _get_eval_after_move(sf_instance, fen, uci_move):
    """Helper to get SAN, numeric evaluation, and eval type after a move."""
    san_move = "N/A"
    numeric_eval = None
    eval_type = None  # To store 'cp' or 'mate'
    try:
        if "uci_to_san" in globals() and callable(uci_to_san):
            san_move = uci_to_san(fen, uci_move)
        else:
            san_move = uci_move
    except Exception:
        san_move = f"{uci_move} (Invalid?)"
    try:
        if sf_instance.is_move_correct(uci_move):
            sf_instance.make_moves_from_current_position([uci_move])
            evaluation = sf_instance.get_evaluation()
            sf_instance.set_fen_position(fen)
            if evaluation:
                eval_type = evaluation.get("type")
                value = evaluation.get("value")
                if isinstance(value, (int, float)) and not math.isnan(value) and not math.isinf(value):
                    numeric_eval = value
                else:
                    st.warning(f"Invalid eval value for {uci_move}: {value}")
        else:
            san_move = f"{san_move} (Illegal)"
    except Exception as e:
        st.warning(f"Stockfish error evaluating {uci_move}: {e}")
        sf_instance.set_fen_position(fen)
    return san_move, numeric_eval, eval_type


@st.cache_data(show_spinner="Analyzing with Stockfish...")
def get_stockfish_analysis(fen, base_uci, target_uci):
    """
    Analyzes the position with Stockfish only for Base and Target moves.
    Ensures each unique move is evaluated only once.
    Returns a dictionary with structured results for 'base' and 'target'.
    """
    # Only include base and target in the results structure
    final_results = {
        "base": {"uci": base_uci, "san": "N/A", "eval": None, "eval_type": None},
        "target": {"uci": target_uci, "san": "N/A", "eval": None, "eval_type": None},
        # No "stockfish1" key anymore
    }
    eval_cache = {}  # Cache results keyed by UCI

    stockfish_path = settings.stockfish_executable
    stockfish_depth = settings.stockfish_depth

    try:
        sf = Stockfish(path=stockfish_path, depth=stockfish_depth)
        if not sf.is_fen_valid(fen):
            st.warning(f"Invalid FEN provided to Stockfish: {fen}")
            return None
        sf.set_fen_position(fen)

        # --- Determine Unique Moves to Evaluate (Base and Target only) ---
        ucis_to_evaluate = set(filter(None, [base_uci, target_uci]))  # Removed sf1_uci

        # --- Evaluate Each Unique Move Once ---
        if not ucis_to_evaluate:
            st.info("No valid Base or Target moves to evaluate.")
        else:
            for uci in ucis_to_evaluate:
                if uci not in eval_cache:
                    san, num_eval, eval_type = _get_eval_after_move(sf, fen, uci)
                    eval_cache[uci] = (san, num_eval, eval_type)

        # --- Populate Final Results from Cache ---
        if base_uci and base_uci in eval_cache:
            san, num_eval, eval_type = eval_cache[base_uci]
            final_results["base"]["san"] = san
            final_results["base"]["eval"] = num_eval
            final_results["base"]["eval_type"] = eval_type
        elif base_uci:
            final_results["base"]["san"] = f"{base_uci} (Eval Failed)"

        if target_uci and target_uci in eval_cache:
            san, num_eval, eval_type = eval_cache[target_uci]
            final_results["target"]["san"] = san
            final_results["target"]["eval"] = num_eval
            final_results["target"]["eval_type"] = eval_type
        elif target_uci:
            final_results["target"]["san"] = f"{target_uci} (Eval Failed)"

        return final_results

    except Exception as e:
        st.error(f"Failed Stockfish analysis setup or execution: {e}")
        return None
