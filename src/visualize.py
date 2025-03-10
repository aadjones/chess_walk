import os
import sys

# Add the root directory to sys.path before any imports
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import chess
import chess.svg
import pandas as pd

from parameters import DIVERGENCE_THRESHOLD  # Import the threshold
from src.logger import logger


def visualize_puzzles(csv_path="output/puzzles.csv", output_html="output/puzzle_visualization.html"):
    """
    Generates an HTML file visualizing the puzzles stored in the CSV with two side-by-side tables,
    sorted by move frequency.

    Args:
        csv_path (str): Path to the CSV file containing puzzles.
        output_html (str): Path to the output HTML file.
    """
    if not pd.io.common.file_exists(csv_path):
        logger.warning(f"No puzzles found at {csv_path} to visualize.")
        return

    try:
        df = pd.read_csv(csv_path, index_col=[0, 1, 2])  # Expect three-level index: Cohort, Row, PuzzleIdx
        unique_puzzle_indices = df.index.get_level_values("PuzzleIdx").unique()
    except Exception as e:
        logger.error(f"Error reading puzzles.csv: {e}. Cannot visualize puzzles.")
        return

    # Start HTML content with improved CSS for styling and WDL bar
    html_content = """
    <html>
    <head>
        <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap" rel="stylesheet">
        <style>
            body {
                font-family: 'Roboto', sans-serif;
                margin: 40px;
                background-color: #f5f5f5;
            }
            h1 {
                text-align: center;
                color: #333;
            }
            h2 {
                color: #444;
                text-align: center;
                margin-top: 40px;
            }
            .chess-board {
                text-align: center;
                margin: 30px 0;
                padding: 10px;
                background-color: #fff;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            }
            .metadata {
                text-align: center;
                color: #777;
                font-style: italic;
                margin: 10px 0;
            }
            .tables-container {
                display: flex;
                justify-content: center;
                gap: 40px;
                margin-top: 20px;
                flex-wrap: wrap;
            }
            .table-wrapper {
                max-width: 500px;
                background-color: #fff;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                padding: 20px;
            }
            h3 {
                text-align: center;
                margin-bottom: 15px;
                color: #555;
                font-size: 1.2em;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 10px;
                text-align: center;
                font-size: 0.9em;
            }
            th {
                background-color: #4CAF50;
                color: white;
                font-weight: 700;
            }
            tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            tr:hover {
                background-color: #f1f1f1;
            }
            .highlight {
                background-color: #ffebcc;
                font-weight: bold;
            }
            /* WDL Bar */
            .wdl-bar {
                display: flex;
                width: 100%;
                height: 10px;
                background: transparent;
            }
            .wdl-white {
                background-color: #ffffff;
                height: 100%;
            }
            .wdl-draw {
                background-color: #cccccc;
                height: 100%;
            }
            .wdl-black {
                background-color: #333333;
                height: 100%;
            }
            /* Tooltip for highlight explanation */
            .table-wrapper:hover .tooltip {
                visibility: visible;
                opacity: 1;
            }
            .tooltip {
                visibility: hidden;
                opacity: 0;
                background-color: #333;
                color: #fff;
                text-align: center;
                padding: 5px 10px;
                border-radius: 5px;
                position: absolute;
                z-index: 1;
                bottom: 100%;
                left: 50%;
                transform: translateX(-50%);
                transition: opacity 0.3s;
            }
            .table-wrapper:hover .tooltip {
                visibility: visible;
                opacity: 0.9;
            }
        </style>
    </head>
    <body>
        <h1>Chess Divergence Puzzles</h1>
    """

    for puzzle_idx in unique_puzzle_indices:
        puzzle_data = df.xs(puzzle_idx, level="PuzzleIdx")
        base_data = puzzle_data.loc["base"].sort_values(by="Freq", ascending=False)
        target_data = puzzle_data.loc["target"].sort_values(by="Freq", ascending=False)

        fen = base_data.iloc[0]["FEN"]
        base_rating = base_data.iloc[0]["Rating"]
        target_rating = target_data.iloc[0]["Rating"]
        ply = base_data.iloc[0]["Ply"] if "Ply" in base_data else "Unknown"
        divergence_gap = base_data.iloc[0]["DivergenceGap"] if "DivergenceGap" in base_data else "Unknown"

        # Create chess board visualization
        board = chess.Board(fen)
        board_svg = chess.svg.board(board=board, size=400)

        # Add puzzle header, metadata, and board
        html_content += f"<h2>Puzzle {puzzle_idx}</h2>"
        html_content += f"<div class='metadata'>Ply: {ply} | Divergence Gap: {divergence_gap}</div>"
        html_content += f"<div class='metadata'>FEN: {fen}</div>"
        html_content += f"<div class='chess-board'>{board_svg}</div>"

        # Add tooltip for highlight explanation
        html_content += """
        <div class='tables-container' style='position: relative;'>
            <div class='table-wrapper' style='position: relative;'>
                <div class='tooltip'>Highlighted rows indicate moves with a frequency difference ≥ 0.5 between cohorts.</div>
        """

        # Base cohort table
        html_content += f"<h3>Base Cohort ({base_rating})</h3>"
        html_content += "<table>"
        html_content += "<tr><th>Move</th><th>Games</th><th>White / Draw / Black</th><th>Frequency</th></tr>"

        base_freqs = {row["Move"]: row["Freq"] for _, row in base_data.iterrows()}
        target_freqs = {row["Move"]: row["Freq"] for _, row in target_data.iterrows()}
        logger.debug(f"Base freqs: {base_freqs}")
        logger.debug(f"Target freqs: {target_freqs}")

        for _, row in base_data.iterrows():
            move = row["Move"]
            target_freq = target_freqs.get(move, 0)
            freq_diff = abs(row["Freq"] - target_freq)
            logger.debug(f"Move: {move}, Base Freq: {row['Freq']}, Target Freq: {target_freq}, Diff: {freq_diff}")
            highlight_class = "highlight" if freq_diff >= DIVERGENCE_THRESHOLD else ""
            html_content += (
                f"<tr class='{highlight_class}'>"
                f"<td>{row['Move']}</td>"
                f"<td>{row['Games']}</td>"
                f"<td>"
                f"<div class='wdl-bar'>"
                f"<div class='wdl-white' style='width: {row['White %']}%;'></div>"
                f"<div class='wdl-draw' style='width: {row['Draw %']}%;'></div>"
                f"<div class='wdl-black' style='width: {row['Black %']}%;'></div>"
                f"</div>"
                f"<div>{row['White %']:.1f}% / {row['Draw %']:.1f}% / {row['Black %']:.1f}%</div>"
                f"</td>"
                f"<td>{row['Freq']:.4f}</td>"
                f"</tr>"
            )
        html_content += "</table></div>"

        # Target cohort table
        html_content += "<div class='table-wrapper' style='position: relative;'>"
        html_content += "<div class='tooltip'>Highlighted rows indicate moves with a frequency difference ≥ 0.5 between cohorts.</div>"
        html_content += f"<h3>Target Cohort ({target_rating})</h3>"
        html_content += "<table>"
        html_content += "<tr><th>Move</th><th>Games</th><th>White / Draw / Black</th><th>Frequency</th></tr>"
        for _, row in target_data.iterrows():
            move = row["Move"]
            base_freq = base_freqs.get(move, 0)
            freq_diff = abs(row["Freq"] - base_freq)
            highlight_class = "highlight" if freq_diff >= DIVERGENCE_THRESHOLD else ""
            html_content += (
                f"<tr class='{highlight_class}'>"
                f"<td>{row['Move']}</td>"
                f"<td>{row['Games']}</td>"
                f"<td>"
                f"<div class='wdl-bar'>"
                f"<div class='wdl-white' style='width: {row['White %']}%;'></div>"
                f"<div class='wdl-draw' style='width: {row['Draw %']}%;'></div>"
                f"<div class='wdl-black' style='width: {row['Black %']}%;'></div>"
                f"</div>"
                f"<div>{row['White %']:.1f}% / {row['Draw %']:.1f}% / {row['Black %']:.1f}%</div>"
                f"</td>"
                f"<td>{row['Freq']:.4f}</td>"
                f"</tr>"
            )
        html_content += "</table></div>"
        html_content += "</div>"  # Close tables-container

    html_content += "</body></html>"

    with open(output_html, "w") as f:
        f.write(html_content)
    logger.info(f"Visualizations saved to {output_html}")


def main():
    """
    Main function to run the visualization script standalone.
    """
    visualize_puzzles()


if __name__ == "__main__":
    main()
