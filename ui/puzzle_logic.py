# puzzle_logic.py
"""Core logic for processing selected puzzle data, including Stockfish analysis."""

import chess
import pandas as pd
import streamlit as st
import os
import sys
from stockfish import Stockfish # Import Stockfish library
import math # For checking NaN/inf in evaluations

# Path setup for src/chess_utils (adjust if your structure differs)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from src.chess_utils import generate_board_svg_with_arrows, uci_to_san
except ImportError:
    st.error("Could not import `chess_utils`. Please ensure `src/chess_utils.py` exists relative to the app's execution directory or adjust `sys.path`.")
    def generate_board_svg_with_arrows(fen, base_uci, target_uci, size): return None
    def uci_to_san(fen, uci): return uci # Fallback

# Import the single settings instance from config.py
from config import settings

# --- Data Retrieval (keep get_puzzle_data as is) ---
def get_puzzle_data(puzzle_groups, current_puzzle_id):
    """Retrieve and process data for the selected puzzle."""
    if current_puzzle_id is None or puzzle_groups is None: return None
    try:
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

# --- Board and Move Preparation (keep prepare_board_data as is) ---
def prepare_board_data(puzzle_df):
    """
    Prepare chessboard data including FEN, SVG, and extract top base/target UCI moves.
    Returns: board, svg_board, base_data_df, target_data_df, base_uci, target_uci
    """
    if puzzle_df is None or puzzle_df.empty:
        st.error("Cannot prepare board data: Puzzle data is missing.")
        return None, None, pd.DataFrame(), pd.DataFrame(), None, None
    if settings.col_fen not in puzzle_df.columns:
        st.error(f"'{settings.col_fen}' column missing in puzzle data.")
        return None, None, pd.DataFrame(), pd.DataFrame(), None, None
    fen = puzzle_df[settings.col_fen].iloc[0]
    try: board = chess.Board(fen)
    except ValueError:
        st.error(f"Invalid FEN string encountered: {fen}")
        return None, None, pd.DataFrame(), pd.DataFrame(), None, None
    base_data = puzzle_df[puzzle_df[settings.col_cohort] == settings.base_cohort_id].copy()
    target_data = puzzle_df[puzzle_df[settings.col_cohort] == settings.target_cohort_id].copy()
    if settings.col_freq in base_data.columns: base_data.sort_values(settings.col_freq, ascending=False, inplace=True)
    if settings.col_freq in target_data.columns: target_data.sort_values(settings.col_freq, ascending=False, inplace=True)
    base_top_uci = None
    if not base_data.empty and settings.col_move in base_data.columns: base_top_uci = base_data[settings.col_move].iloc[0]
    target_top_uci = None
    if not target_data.empty and settings.col_move in target_data.columns: target_top_uci = target_data[settings.col_move].iloc[0]
    svg_board = None
    try:
        if 'generate_board_svg_with_arrows' in globals() and callable(generate_board_svg_with_arrows):
             svg_board = generate_board_svg_with_arrows(fen=fen, base_uci=base_top_uci, target_uci=target_top_uci, size=500)
        else: st.warning("SVG generation function not available.")
    except Exception as e: st.error(f"Error generating board SVG: {e}")
    return board, svg_board, base_data, target_data, base_top_uci, target_top_uci

# --- Move Conversion (keep convert_moves_to_san as is) ---
def convert_moves_to_san(base_data, target_data, fen):
    """Convert UCI moves to SAN notation for display."""
    if fen is None: st.error("Cannot convert moves to SAN: FEN string is missing."); return base_data, target_data
    if 'uci_to_san' not in globals() or not callable(uci_to_san): st.warning("uci_to_san function not available..."); return base_data, target_data
    def _safe_uci_to_san(move_uci):
        if pd.isna(move_uci): return None
        try: return uci_to_san(fen, move_uci)
        except Exception as e: st.warning(f"Could not convert UCI '{move_uci}': {e}"); return move_uci
    move_col = settings.col_move
    if base_data is not None and not base_data.empty and move_col in base_data.columns: base_data.loc[:, move_col] = base_data[move_col].apply(_safe_uci_to_san)
    if target_data is not None and not target_data.empty and move_col in target_data.columns: target_data.loc[:, move_col] = target_data[move_col].apply(_safe_uci_to_san)
    return base_data, target_data

# --- Stockfish Analysis (Revised: Evaluate Unique Moves Once) ---

def _get_eval_after_move(sf_instance, fen, uci_move):
    """Helper to get SAN, numeric evaluation, and eval type after a move."""
    san_move = "N/A"
    numeric_eval = None
    eval_type = None # To store 'cp' or 'mate'

    # Attempt to convert UCI to SAN first
    try:
        if 'uci_to_san' in globals() and callable(uci_to_san): san_move = uci_to_san(fen, uci_move)
        else: san_move = uci_move # Fallback
    except Exception: san_move = f"{uci_move} (Invalid?)"

    try:
        if sf_instance.is_move_correct(uci_move):
            sf_instance.make_moves_from_current_position([uci_move])
            evaluation = sf_instance.get_evaluation()
            sf_instance.set_fen_position(fen) # IMPORTANT: Reset position

            if evaluation:
                eval_type = evaluation.get("type")
                value = evaluation.get("value")
                if isinstance(value, (int, float)) and not math.isnan(value) and not math.isinf(value):
                    numeric_eval = value
                else: st.warning(f"Invalid eval value for {uci_move}: {value}")
        else:
             san_move = f"{san_move} (Illegal)"
    except Exception as e:
        st.warning(f"Stockfish error evaluating {uci_move}: {e}")
        sf_instance.set_fen_position(fen) # Ensure reset on error

    return san_move, numeric_eval, eval_type


@st.cache_data(show_spinner="Analyzing with Stockfish...")
def get_stockfish_analysis(fen, base_uci, target_uci):
    """
    Analyzes the position with Stockfish for Base, Target, and Top 1 engine moves.
    Ensures each unique move is evaluated only once.
    Returns a dictionary with structured results.
    """
    final_results = {
        "base": {"uci": base_uci, "san": "N/A", "eval": None, "eval_type": None},
        "target": {"uci": target_uci, "san": "N/A", "eval": None, "eval_type": None},
        "stockfish1": {"uci": None, "san": "N/A", "eval": None, "eval_type": None}
    }
    eval_cache = {} # Cache results keyed by UCI: {'uci': (san, eval, type)}
    sf1_uci = None # Placeholder for Stockfish #1 move UCI

    stockfish_path = settings.stockfish_executable
    stockfish_depth = settings.stockfish_depth

    try:
        # Initialize Stockfish
        sf = Stockfish(path=stockfish_path, depth=stockfish_depth)
        if not sf.is_fen_valid(fen):
            st.warning(f"Invalid FEN provided to Stockfish: {fen}")
            return None
        sf.set_fen_position(fen)

        # --- Get Top 1 Stockfish Move UCI ---
        try:
            top_moves_info = sf.get_top_moves(1)
            if top_moves_info:
                sf1_uci = top_moves_info[0].get("Move")
                final_results["stockfish1"]["uci"] = sf1_uci # Store the UCI
            else:
                 st.info("Stockfish did not return a top move.")
        except Exception as e:
            st.warning(f"Stockfish error getting top move: {e}")

        # --- Determine Unique Moves to Evaluate ---
        # Filter out None values before creating the set
        ucis_to_evaluate = set(filter(None, [base_uci, target_uci, sf1_uci]))

        # --- Evaluate Each Unique Move Once ---
        if not ucis_to_evaluate:
             st.info("No valid moves (Base, Target, Stockfish #1) to evaluate.")
        else:
            for uci in ucis_to_evaluate:
                if uci not in eval_cache: # Evaluate only if not already cached
                    san, num_eval, eval_type = _get_eval_after_move(sf, fen, uci)
                    eval_cache[uci] = (san, num_eval, eval_type)

        # --- Populate Final Results from Cache ---
        if base_uci and base_uci in eval_cache:
            san, num_eval, eval_type = eval_cache[base_uci]
            final_results["base"]["san"] = san
            final_results["base"]["eval"] = num_eval
            final_results["base"]["eval_type"] = eval_type
        elif base_uci: # Handle case where base_uci existed but evaluation failed
             final_results["base"]["san"] = f"{base_uci} (Eval Failed)"

        if target_uci and target_uci in eval_cache:
            san, num_eval, eval_type = eval_cache[target_uci]
            final_results["target"]["san"] = san
            final_results["target"]["eval"] = num_eval
            final_results["target"]["eval_type"] = eval_type
        elif target_uci:
             final_results["target"]["san"] = f"{target_uci} (Eval Failed)"

        if sf1_uci and sf1_uci in eval_cache:
            san, num_eval, eval_type = eval_cache[sf1_uci]
            final_results["stockfish1"]["san"] = san
            final_results["stockfish1"]["eval"] = num_eval
            final_results["stockfish1"]["eval_type"] = eval_type
        elif sf1_uci: # Handle case where sf1_uci existed but evaluation failed
            final_results["stockfish1"]["san"] = f"{sf1_uci} (Eval Failed)"
        # If sf1_uci itself is None, defaults remain "N/A"

        return final_results

    except Exception as e:
        st.error(f"Failed Stockfish analysis setup or execution: {e}")
        return None # Indicate failure