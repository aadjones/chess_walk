import pandas as pd

from src.walker import save_position_to_csv


def create_sample_df(
    position_idx: int, fen: str, cohort: str, row: int, rating: str, ply: int, cohort_pair: str
) -> pd.DataFrame:
    """
    Creates a sample DataFrame mimicking position data.
    Sets a multi-index for Cohort, Row, PositionIdx.
    """
    data = {
        "FEN": [fen],
        "Rating": [rating],
        "Ply": [ply],
        "CohortPair": [cohort_pair],
        "Move": ["e2e4"],
        "Games": [100],
        "White %": [50.0],
        "Draw %": [30.0],
        "Black %": [20.0],
        "Freq": [0.6],
    }
    df = pd.DataFrame(data)
    # Create multi-index for Cohort, Row, PositionIdx
    df.index = pd.MultiIndex.from_tuples([(cohort, row, position_idx)], names=["Cohort", "Row", "PositionIdx"])
    return df


def test_save_position_to_csv_new(tmp_path):
    """
    Test that saving a new position to a non-existing CSV creates a file with one unique PuzzleIdx.
    """
    output_csv = tmp_path / "positions.csv"
    df_new = create_sample_df(
        position_idx=0, fen="fen1", cohort="base", row=0, rating="1200", ply=5, cohort_pair="1200-1600"
    )
    save_position_to_csv(df_new, output_path=str(output_csv))
    df_loaded = pd.read_csv(str(output_csv), index_col=[0, 1, 2])
    unique_indices = df_loaded.index.get_level_values("PositionIdx").unique()
    assert len(unique_indices) == 1, f"Expected 1 unique PositionIdx, got {len(unique_indices)}"


def test_save_position_to_csv_skip_duplicate(tmp_path):
    """
    Test that if a position with the same FEN and same CohortPair is saved, it is skipped.
    """
    output_csv = tmp_path / "positions.csv"
    # Write an initial position row.
    df_initial = create_sample_df(
        position_idx=0, fen="fen_duplicate", cohort="base", row=0, rating="1200", ply=5, cohort_pair="1200-1600"
    )
    df_initial.to_csv(str(output_csv))

    # Create a new position with the same FEN and same CohortPair.
    df_duplicate = create_sample_df(
        position_idx=99, fen="fen_duplicate", cohort="base", row=0, rating="1200", ply=5, cohort_pair="1200-1600"
    )
    save_position_to_csv(df_duplicate, output_path=str(output_csv))

    df_loaded = pd.read_csv(str(output_csv), index_col=[0, 1, 2])
    unique_indices = df_loaded.index.get_level_values("PositionIdx").unique()
    # The duplicate should be skipped, so unique PositionIdx remains 1.
    assert len(unique_indices) == 1, f"Expected 1 unique PositionIdx, got {len(unique_indices)}"


def test_save_position_to_csv_append_non_duplicate(tmp_path):
    """
    Test that saving a position with a different FEN (or different CohortPair) appends a new row.
    """
    output_csv = tmp_path / "positions.csv"
    # Write an initial position row.
    df_initial = create_sample_df(
        position_idx=0, fen="fen1", cohort="base", row=0, rating="1200", ply=5, cohort_pair="1200-1600"
    )
    df_initial.to_csv(str(output_csv))

    # Create a new position with a different FEN.
    df_new = create_sample_df(
        position_idx=99, fen="fen2", cohort="base", row=0, rating="1200", ply=5, cohort_pair="1200-1600"
    )
    save_position_to_csv(df_new, output_path=str(output_csv))

    df_loaded = pd.read_csv(str(output_csv), index_col=[0, 1, 2])
    unique_indices = df_loaded.index.get_level_values("PositionIdx").unique()
    # We expect 2 unique PositionIdx values.
    assert len(unique_indices) == 2, f"Expected 2 unique PositionIdx, got {len(unique_indices)}"
