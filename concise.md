```markdown
The folder contains a set of Python modules designed to analyze chess positions and generate puzzles based on statistical divergences in move choices between different rating cohorts. The key functionalities include:

- **API Interaction**: `api.py` provides functions to fetch move statistics from the Lichess Explorer API.
- **Chess Utilities**: `chess_utils.py` offers utilities for converting chess moves and generating SVG representations of chess boards.
- **CSV Management**: `csv_utils.py` includes functions for sorting and managing CSV files containing chess data.
- **Logging**: `logger.py` sets up a logging system to track the application's operations.
- **Statistical Analysis**: `divergence.py` contains functions to perform statistical tests (chi-square and Z-test) to identify significant differences in move frequencies and win rates between cohorts.
- **Puzzle Generation**: `walker.py` implements a random walk through chess positions to evaluate and save positions with significant divergences as puzzles.

These modules collectively support the analysis of chess games to identify and document strategic differences across player skill levels.
```
