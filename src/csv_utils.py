import pandas as pd


def sort_csv(input_path: str = "output/positions.csv", output_path: str = "output/positions.csv") -> None:
    """
    Reads a CSV file from input_path, sorts the rows by the lower bound of the rating
    in the 'CohortPair' column, and writes the sorted DataFrame to output_path.

    Parameters:
        input_path (str): Path to the input CSV file.
        output_path (str): Path where the sorted CSV file will be saved. Defaults to in place.
    """
    # Load the CSV file into a DataFrame
    df = pd.read_csv(input_path)

    # Create a helper column 'lower_bound' by extracting the lower rating from 'CohortPair'
    df["lower_bound"] = df["CohortPair"].apply(lambda x: int(x.split("-")[0]))

    # Sort the DataFrame by the 'lower_bound'
    df.sort_values(by="lower_bound", inplace=True)

    # Optionally, remove the helper column if no longer needed
    df.drop(columns=["lower_bound"], inplace=True)

    # Write the sorted DataFrame back to a CSV file
    df.to_csv(output_path, index=False)
