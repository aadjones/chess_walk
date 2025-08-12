import pandas as pd

from src.csv_utils import sort_csv


def test_sort_csv(tmp_path):
    # Create sample unsorted CSV data as a multi-line string.
    csv_content = (
        "Cohort,Row,PositionIdx,Move,Games,White %,Draw %,Black %,Freq,FEN,Rating,Ply,CohortPair\n"
        "base,0,0,f3g5,100,45,5,50,0.2,some_fen,1200,6,1400-1800\n"
        "base,1,0,f3g5,100,45,5,50,0.2,some_fen,1200,6,1200-1600\n"
        "base,2,0,f3g5,100,45,5,50,0.2,some_fen,1200,6,2000-2500\n"
        "base,3,0,f3g5,100,45,5,50,0.2,some_fen,1200,6,1000-1400\n"
    )

    # Write the unsorted CSV to a temporary file.
    input_file = tmp_path / "positions.csv"
    input_file.write_text(csv_content)

    # Define the output file path in the temporary directory.
    output_file = tmp_path / "positions_sorted.csv"

    # Call your sort_csv function.
    sort_csv(input_path=str(input_file), output_path=str(output_file))

    # Read the sorted CSV.
    sorted_df = pd.read_csv(output_file)

    # Extract the CohortPair column to check the order.
    sorted_cohorts = list(sorted_df["CohortPair"])

    # Expected order is based on the lower bound of the CohortPair (e.g., "1000-1400" should come first).
    expected_order = ["1000-1400", "1200-1600", "1400-1800", "2000-2500"]

    # Assert that the output is as expected.
    assert sorted_cohorts == expected_order, f"Expected {expected_order} but got {sorted_cohorts}"
