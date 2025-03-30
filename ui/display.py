# display.py
"""Handles the layout and display of the main application content."""

import streamlit as st
import pandas as pd
import math # For checking numeric types and NaN/inf
from session_state_utils import toggle_stockfish_display
from config import settings

def format_eval_for_display(numeric_eval, eval_type):
    """Formats numeric evaluation (cp or mate) into a string for display."""
    if numeric_eval is None:
        return "N/A"

    if eval_type == "cp":
        if isinstance(numeric_eval, (int, float)) and not math.isnan(numeric_eval) and not math.isinf(numeric_eval):
             pawn_value = numeric_eval / 100.0
             return f"{pawn_value:+.2f}"
        else:
             return "Invalid"
    elif eval_type == "mate":
        if isinstance(numeric_eval, (int, float)) and not math.isnan(numeric_eval) and not math.isinf(numeric_eval):
            mate_val = int(numeric_eval)
            prefix = "+" if mate_val > 0 else ""
            return f"Mate {prefix}{abs(mate_val)}" if mate_val !=0 else "Mate"
        else:
             return "Invalid"
    else: # Fallback
        try:
            pawn_value = float(numeric_eval) / 100.0
            return f"{pawn_value:+.2f}"
        except (ValueError, TypeError):
             return "Unknown"

def display_stockfish_comparison(analysis_results):
    """Displays the Stockfish analysis using markdown and columns for a clean look."""
    if not analysis_results:
        st.info("Stockfish analysis is not available or failed.")
        return

    st.markdown("#### Stockfish Evaluation Comparison")
    st.caption("_(Eval after move, from White's perspective)_")
    st.write("") # Add a little vertical space

    # Extract data with defaults
    base_info = analysis_results.get("base", {})
    target_info = analysis_results.get("target", {})
    sf1_info = analysis_results.get("stockfish1", {})

    # Get SAN moves - handle potential " (Illegal)" suffix from evaluation step
    def clean_san(san_string):
        if san_string is None: return "N/A"
        # Simple cleaning, might need adjustment if other tags appear
        return san_string.split(" (")[0]

    base_san = clean_san(base_info.get("san", "N/A"))
    base_eval_num = base_info.get("eval")
    base_eval_type = base_info.get("eval_type")
    base_eval_str = format_eval_for_display(base_eval_num, base_eval_type)

    target_san = clean_san(target_info.get("san", "N/A"))
    target_eval_num = target_info.get("eval")
    target_eval_type = target_info.get("eval_type")
    target_eval_str = format_eval_for_display(target_eval_num, target_eval_type)

    sf1_san = clean_san(sf1_info.get("san", "N/A"))
    sf1_eval_num = sf1_info.get("eval")
    sf1_eval_type = sf1_info.get("eval_type")
    sf1_eval_str = format_eval_for_display(sf1_eval_num, sf1_eval_type)

    # --- Create Columns using Markdown ---
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Base**")
        # Use larger font size for move, colored red
        st.markdown(f"<span style='color:red; font-size: 1.2em;'>**{base_san}**</span>", unsafe_allow_html=True)
        st.markdown(f"{base_eval_str}")

    with col2:
        st.markdown("**Target**")
        # Use larger font size for move, colored blue
        st.markdown(f"<span style='color:blue; font-size: 1.2em;'>**{target_san}**</span>", unsafe_allow_html=True)
        st.markdown(f"{target_eval_str}")

    with col3:
        st.markdown("**Stockfish #1**")
        # Use larger font size for move, default color
        st.markdown(f"<span style='font-size: 1.2em;'>**{sf1_san}**</span>", unsafe_allow_html=True)
        st.markdown(f"{sf1_eval_str}")

    st.divider() # Keep the divider

    # --- Calculate and Display Delta with Clearer Text ---
    delta_str = "N/A"
    # Calculate delta only if both evaluations are valid centipawn numbers
    if (base_eval_type == "cp" and isinstance(base_eval_num, (int, float)) and
        target_eval_type == "cp" and isinstance(target_eval_num, (int, float)) and
        not math.isnan(base_eval_num) and not math.isinf(base_eval_num) and
        not math.isnan(target_eval_num) and not math.isinf(target_eval_num)):
        try:
            delta = abs((target_eval_num / 100.0) - (base_eval_num / 100.0))
            delta_str = f"**{delta:.2f} pawns**" # Make value bold
        except Exception:
            delta_str = "**Error**"
    elif base_eval_type == "mate" or target_eval_type == "mate":
        delta_str = "*(Mate involved)*" # Simpler text
    else:
        delta_str = "*(N/A)*" # Simpler text

    # Use clearer label
    st.markdown(f"Cohort Move Difference: {delta_str}")


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
             # Call the new markdown-based display function
             display_stockfish_comparison(stockfish_results) # <<< RENAMED function call


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