# display.py
"""Handles the layout and display of the main application content."""

import streamlit as st
import pandas as pd
import math # For checking numeric types and NaN/inf
import chess # Import python-chess to parse FEN
from session_state_utils import toggle_stockfish_display
from config import settings

def format_eval_for_display(numeric_eval, eval_type):
    """Formats numeric evaluation (cp or mate) into a string for display."""
    if numeric_eval is None: return "N/A"
    if eval_type == "cp":
        if isinstance(numeric_eval, (int, float)) and not math.isnan(numeric_eval) and not math.isinf(numeric_eval):
             return f"{numeric_eval / 100.0:+.2f}"
        else: return "Invalid"
    elif eval_type == "mate":
        if isinstance(numeric_eval, (int, float)) and not math.isnan(numeric_eval) and not math.isinf(numeric_eval):
            mate_val = int(numeric_eval)
            prefix = "+" if mate_val > 0 else ""
            return f"Mate {prefix}{abs(mate_val)}" if mate_val !=0 else "Mate"
        else: return "Invalid"
    else:
        try: return f"{float(numeric_eval) / 100.0:+.2f}"
        except (ValueError, TypeError): return "Unknown"

def display_stockfish_comparison(analysis_results, fen): # Added fen argument
    """Displays the Stockfish analysis for Base vs Target using markdown and columns."""
    if not analysis_results:
        st.info("Stockfish analysis is not available or failed.")
        return

    st.markdown("#### Cohort Move Evaluation") # Simplified Title
    st.caption("_(Eval after move, from White's perspective)_")
    st.write("") # Add a little vertical space

    turn = None
    if fen:
        try:
            board = chess.Board(fen)
            turn = board.turn
        except ValueError:
            st.warning("Invalid FEN provided, cannot determine turn for delta interpretation.")
            turn = None

    # Extract data - only need base and target now
    base_info = analysis_results.get("base", {})
    target_info = analysis_results.get("target", {})

    def clean_san(san_string):
        if san_string is None: return "N/A"
        return san_string.split(" (")[0]

    base_san = clean_san(base_info.get("san", "N/A"))
    base_eval_num = base_info.get("eval")
    base_eval_type = base_info.get("eval_type")
    base_eval_str = format_eval_for_display(base_eval_num, base_eval_type)

    target_san = clean_san(target_info.get("san", "N/A"))
    target_eval_num = target_info.get("eval")
    target_eval_type = target_info.get("eval_type")
    target_eval_str = format_eval_for_display(target_eval_num, target_eval_type)

    # --- Create 2 Columns using Markdown ---
    col1, col2 = st.columns(2) # Use only 2 columns

    with col1:
        st.markdown("**Base**")
        st.markdown(f"<span style='color:red; font-size: 1.2em;'>**{base_san}**</span>", unsafe_allow_html=True)
        st.markdown(f"{base_eval_str}")

    with col2:
        st.markdown("**Target**")
        st.markdown(f"<span style='color:blue; font-size: 1.2em;'>**{target_san}**</span>", unsafe_allow_html=True)
        st.markdown(f"{target_eval_str}")

    # Removed the 3rd column for Stockfish #1

    st.divider()

    # --- Calculate and Display Delta based on Turn ---
    delta_value_part = "N/A"
    label_prefix = ""

    if (base_eval_type == "cp" and isinstance(base_eval_num, (int, float)) and
        target_eval_type == "cp" and isinstance(target_eval_num, (int, float)) and
        not math.isnan(base_eval_num) and not math.isinf(base_eval_num) and
        not math.isnan(target_eval_num) and not math.isinf(target_eval_num)):
        try:
            raw_delta = (target_eval_num / 100.0) - (base_eval_num / 100.0)
            display_delta = 0.0
            label_prefix = "Unknown Turn = "

            if turn == chess.WHITE:
                display_delta = raw_delta
                label_prefix = f"<span style='color:blue'>Blue</span> - <span style='color:red'>Red</span> = "
            elif turn == chess.BLACK:
                display_delta = -raw_delta
                label_prefix = f"<span style='color:red'>Red</span> - <span style='color:blue'>Blue</span> = "
            else: # FEN invalid or missing
                display_delta = raw_delta
                label_prefix = "Blue - Red (Turn Unknown) = "

            delta_color = "blue" if display_delta >= 0 else "red"
            formatted_delta = f"{display_delta:+.2f}"
            delta_value_part = f"<span style='color:{delta_color}'>**{formatted_delta} pawns**</span>"

        except Exception:
            delta_value_part = "<span style='color:orange'>**Error**</span>"
    elif base_eval_type == "mate" or target_eval_type == "mate":
        delta_value_part = "*(Mate involved)*"
    else:
        delta_value_part = "*(N/A)*"

    final_markdown_string = label_prefix + delta_value_part
    st.markdown(final_markdown_string, unsafe_allow_html=True)


def layout_main_content(fen, svg_board, base_rating, target_rating, base_display_df, target_display_df, stockfish_results=None):
    """Lay out the board, tables, and Stockfish analysis comparison."""
    left_col, mid_col, right_col = st.columns([3, 4, 4])

    with left_col:
        st.markdown("### Board Position")
        if fen:
            st.markdown(f"**FEN**: `{fen}`")
        if svg_board:
            st.image(svg_board, use_container_width=True)
        else:
            st.warning("Board image could not be generated or is unavailable.")

        # --- Stockfish Button ---
        show_sf = st.session_state.get("show_stockfish", False)
        button_text = "Hide Stockfish Analysis" if show_sf else "Analyze with Stockfish"
        st.button(button_text, key="stockfish_toggle_button", on_click=toggle_stockfish_display)

        # --- Conditional Stockfish Display ---
        if st.session_state.get("show_stockfish", False):
             # Pass FEN to the display function
             display_stockfish_comparison(analysis_results=stockfish_results, fen=fen)

    # --- Right Columns (Mid and Right) remain unchanged ---
    with mid_col:
        st.markdown(f"### Base Cohort ({base_rating})")
        if base_display_df is not None and not base_display_df.empty:
            st.dataframe(base_display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No data available for the Base Cohort.")

    with right_col:
        st.markdown(f"### Target Cohort ({target_rating})")
        if target_display_df is not None and not target_display_df.empty:
            st.dataframe(target_display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No data available for the Target Cohort.")