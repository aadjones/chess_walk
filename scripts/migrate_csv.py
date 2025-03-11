import os

import pandas as pd

# Path to the old CSV file
csv_path = "output/puzzles.csv"

if not os.path.exists(csv_path):
    print("CSV file not found:", csv_path)
    exit(1)

# Load the CSV with the multi-index (Cohort, Row, PuzzleIdx)
try:
    df = pd.read_csv(csv_path, index_col=[0, 1, 2])
except Exception as e:
    print("Error loading CSV:", e)
    exit(1)

# Check if the new column 'CohortPair' exists.
if "CohortPair" not in df.columns:
    # For the old CSV, all puzzles are for 1200 vs 1600, so use that as the default.
    df["CohortPair"] = "1200-1600"
    print("Added 'CohortPair' column with default value '1200-1600'.")
else:
    print("'CohortPair' column already exists.")

# Choose whether to overwrite the existing file or write to a new file.
output_path = "output/puzzles_migrated.csv"  # or csv_path to overwrite
df.to_csv(output_path)
print("Migration complete. Updated CSV saved to", output_path)
