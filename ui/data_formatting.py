# data_formatting.py
"""Functions for cleaning and formatting DataFrames for display."""

import pandas as pd
import streamlit as st  # Only needed if adding warnings/errors here
from config import settings  # Use settings for column names


def cleanup_dataframe(df):
    """Remove unnecessary columns, format types, and set index."""
    if df is None or df.empty:
        return pd.DataFrame()  # Return consistent empty DataFrame

    df_copy = df.copy()  # Work on a copy to avoid SettingWithCopyWarning

    # Columns to potentially drop
    cols_to_drop = [settings.col_cohort, settings.col_position_idx, settings.col_cohort_pair, settings.col_rating]
    # Drop only existing columns
    existing_cols_to_drop = [col for col in cols_to_drop if col in df_copy.columns]
    if existing_cols_to_drop:
        df_copy.drop(columns=existing_cols_to_drop, inplace=True)

    # Format Freq as percentage (numeric for sorting, formatted later)
    freq_col = settings.col_freq
    if freq_col in df_copy.columns:
        # Convert to numeric, coercing errors, then multiply
        df_copy[freq_col] = pd.to_numeric(df_copy[freq_col], errors="coerce") * 100

    # Format Games as integer
    games_col = settings.col_games
    if games_col in df_copy.columns:
        df_copy[games_col] = pd.to_numeric(df_copy[games_col], errors="coerce").fillna(0).astype(int)

    # Sort by Freq (descending) if available and numeric
    if freq_col in df_copy.columns and pd.api.types.is_numeric_dtype(df_copy[freq_col]):
        df_copy.sort_values(freq_col, ascending=False, inplace=True, na_position="last")

    # Reset index to be 1-based for display AFTER sorting
    df_copy.reset_index(drop=True, inplace=True)
    df_copy.index = df_copy.index + 1

    return df_copy


def format_wdl_column(df):
    """Combine W/D/L percentages into a single formatted string column."""
    if df is None or df.empty:
        return df  # Return original if empty or None

    df_copy = df.copy()
    wdl_col = "W/D/L"  # The target column name
    # Source columns from settings
    white_col, draw_col, black_col = settings.col_white_perc, settings.col_draw_perc, settings.col_black_perc
    wdl_source_cols = [white_col, draw_col, black_col]

    if all(col in df_copy.columns for col in wdl_source_cols):
        # Ensure WDL columns are numeric before formatting
        for col in wdl_source_cols:
            df_copy[col] = pd.to_numeric(df_copy[col], errors="coerce").fillna(0.0)

        # Apply formatting row-wise safely
        try:
            df_copy[wdl_col] = df_copy.apply(
                lambda row: f"{row[white_col]:.1f}%/{row[draw_col]:.1f}%/{row[black_col]:.1f}%", axis=1
            )
            # Drop original W/D/L columns AFTER creating the new one
            df_copy = df_copy.drop(columns=wdl_source_cols, errors="ignore")
        except Exception as e:
            # Handle potential errors during apply (though less likely with coercion)
            st.warning(f"Could not format W/D/L column: {e}")
            if wdl_col not in df_copy.columns:  # Ensure column exists even if formatting fails
                df_copy[wdl_col] = "Error"

    elif wdl_col not in df_copy.columns:  # If source columns missing and target missing
        # Add placeholder if needed by display logic, check settings.display_cols
        if wdl_col in settings.display_cols:
            df_copy[wdl_col] = "N/A"

    return df_copy


def infer_rating(df, default_rating="N/A"):
    """Infer rating from the DataFrame, using the first row if available."""
    rating_col = settings.col_rating
    if df is not None and not df.empty and rating_col in df.columns:
        # Use the rating from the first row (assuming consistency per cohort within a puzzle)
        rating = df[rating_col].iloc[0]
        # Check for NaN or None before returning
        return rating if pd.notna(rating) else default_rating
    return default_rating


def prepare_display_dataframe(df):
    """Select and format columns specifically for Streamlit dataframe display."""
    if df is None or df.empty:
        # Return an empty DataFrame with expected columns for consistent layout
        return pd.DataFrame(columns=settings.display_cols)

    df_copy = df.copy()
    display_cols = settings.display_cols
    freq_col = settings.col_freq

    # Ensure only existing columns are selected
    cols_to_display = [col for col in display_cols if col in df_copy.columns]
    display_df = df_copy[cols_to_display].copy()

    # Format Freq column as string with '%' for display
    if freq_col in display_df.columns:
        # Should already be numeric from cleanup, apply formatting
        display_df[freq_col] = display_df[freq_col].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "N/A")
        # Ensure object type for consistent display if needed
        # display_df[freq_col] = display_df[freq_col].astype("object")

    # Ensure all expected display columns exist, even if empty
    for col in display_cols:
        if col not in display_df.columns:
            display_df[col] = "N/A"  # Or pd.NA or suitable placeholder

    # Reorder columns according to settings.display_cols
    display_df = display_df[display_cols]

    return display_df
