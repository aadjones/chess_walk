# data_formatting.py
"""Functions for cleaning and formatting DataFrames for display."""

import pandas as pd
import streamlit as st
from config import (
    COL_COHORT, COL_PUZZLE_IDX, COL_COHORT_PAIR, COL_FREQ, COL_GAMES,
    COL_RATING, COL_WHITE_PERC, COL_DRAW_PERC, COL_BLACK_PERC,
    DISPLAY_COLS
)

def cleanup_dataframe(df):
    """Remove unnecessary columns, format types, and set index."""
    if df is None or df.empty:
        return df

    # Columns to potentially drop
    cols_to_drop = [COL_COHORT, COL_PUZZLE_IDX, COL_COHORT_PAIR, COL_RATING]
    df = df.drop(columns=[col for col in cols_to_drop if col in df.columns], errors='ignore')

    # Format Freq as percentage (numeric for now, display formatting later)
    if COL_FREQ in df.columns:
        df[COL_FREQ] = df[COL_FREQ] * 100

    # Format Games as integer
    if COL_GAMES in df.columns:
        df[COL_GAMES] = pd.to_numeric(df[COL_GAMES], errors='coerce').fillna(0).astype(int)

    # Reset index to be 1-based for display
    df.reset_index(drop=True, inplace=True)
    df.index = df.index + 1

    # Sort by Freq (descending) if available
    if COL_FREQ in df.columns:
        df.sort_values(COL_FREQ, ascending=False, inplace=True)

    return df


def format_wdl_column(df):
    """Combine W/D/L percentages into a single formatted string column."""
    if df is None or df.empty:
        return df

    wdl_cols = [COL_WHITE_PERC, COL_DRAW_PERC, COL_BLACK_PERC]
    if all(col in df.columns for col in wdl_cols):
        # Ensure WDL columns are numeric before formatting
        for col in wdl_cols:
             df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)

        # Apply formatting row-wise
        df['W/D/L'] = df.apply(
            lambda row: f"{row[COL_WHITE_PERC]:.1f}% / {row[COL_DRAW_PERC]:.1f}% / {row[COL_BLACK_PERC]:.1f}%",
            axis=1
        )
        # Drop original W/D/L columns
        df = df.drop(columns=wdl_cols, errors='ignore')
    else:
         # If WDL columns aren't present, add an empty placeholder if needed by DISPLAY_COLS
         if 'W/D/L' in DISPLAY_COLS and 'W/D/L' not in df.columns:
              df['W/D/L'] = "N/A"

    return df


def infer_rating(df, default_rating="N/A"):
    """Infer rating from the DataFrame, using the first row if available."""
    if df is not None and not df.empty and COL_RATING in df.columns:
        # Use the rating from the first row (assuming it's consistent per cohort)
        rating = df[COL_RATING].iloc[0]
        return rating if pd.notna(rating) else default_rating
    return default_rating


def prepare_display_dataframe(df):
    """Select and format columns specifically for Streamlit dataframe display."""
    if df is None or df.empty:
        # Return an empty DataFrame with expected columns for consistent layout
        return pd.DataFrame(columns=DISPLAY_COLS)

    # Ensure only existing columns are selected
    cols_to_display = [col for col in DISPLAY_COLS if col in df.columns]
    display_df = df[cols_to_display].copy()

    # Format Freq column as string with '%'
    if COL_FREQ in display_df.columns:
        # Make sure Freq is numeric before formatting
        display_df[COL_FREQ] = pd.to_numeric(display_df[COL_FREQ], errors='coerce')
        display_df[COL_FREQ] = display_df[COL_FREQ].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A")
        # display_df[COL_FREQ] = display_df[COL_FREQ].astype("object") # Ensure string type if needed

    return display_df