# display.py
"""Handles the layout and display of the main application content."""

import streamlit as st
import pandas as pd # Needed for type hinting or DataFrame checks

def layout_main_content(fen, svg_board, base_rating, target_rating, base_display_df, target_display_df):
    """Lay out the board and tables in a three-column format."""
    if fen is None or svg_board is None:
        st.warning("Board data is incomplete. Cannot display position.")
        # Optionally display tables even if board fails
        # return

    left_col, mid_col, right_col = st.columns([3, 4, 4]) # Adjust ratios as needed

    with left_col:
        st.markdown("### Board Position")
        if fen:
            st.write(f"**FEN**: `{fen}`")
        if svg_board:
            st.image(svg_board, use_container_width=True)
        else:
            st.warning("Board image could not be generated.")

    with mid_col:
        st.markdown(f"### Base Cohort ({base_rating})")
        if base_display_df is not None and not base_display_df.empty:
            st.dataframe(base_display_df, use_container_width=True)
        else:
            st.info("No data available for the Base Cohort.")

    with right_col:
        st.markdown(f"### Target Cohort ({target_rating})")
        if target_display_df is not None and not target_display_df.empty:
            st.dataframe(target_display_df, use_container_width=True)
        else:
            st.info("No data available for the Target Cohort.")