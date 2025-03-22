```markdown
# Chess Position Analysis and Puzzle Generation

This folder is a comprehensive suite of Python modules designed to analyze chess positions and generate puzzles by identifying statistical divergences in move choices across different player rating cohorts. The system is structured into several key components, each serving a specific purpose in the overall workflow:

## Components Overview

### API Interaction
- **Module**: `api.py`
- **Functionality**: Provides functions to fetch move statistics from the Lichess Explorer API, which serves as the foundational data source for the analysis.

### Divergence Analysis
- **Module**: `divergence.py`
- **Functionality**: Performs statistical tests, including chi-square and Z-tests, to identify significant differences in move frequencies and win rates between different rating cohorts. This analysis is crucial for detecting strategic differences in gameplay.

### Walker Pipeline
- **Module**: `walker.py`
- **Functionality**: Implements a random walk through chess positions to evaluate and save positions with significant divergences as puzzles. This pipeline includes:
  - Choosing moves based on weighted probabilities.
  - Evaluating divergence in positions.
  - Validating initial positions.
  - Creating and saving puzzle data.

### Utilities
- **Modules**: `chess_utils.py`, `csv_utils.py`, `logger.py`
- **Functionality**:
  - `chess_utils.py`: Offers utilities for converting chess moves and generating SVG representations of chess boards.
  - `csv_utils.py`: Includes functions for sorting and managing CSV files containing chess data.
  - `logger.py`: Sets up a logging system to track the application's operations, ensuring transparency and traceability.

## Workflow Integration

The system's workflow is depicted in the Mermaid diagram, illustrating how each component interacts:

- **API Layer**: The `get_move_stats` function fetches data and is integral to both the divergence analysis and the walker pipeline.
- **Divergence Analysis**: Functions like `build_move_df`, `check_frequency_divergence`, and `check_win_rate_difference` work together to find divergences, using data fetched from the API.
- **Walker Pipeline**: This pipeline orchestrates the process of generating puzzles, from move selection to puzzle creation and saving, while leveraging the divergence analysis results.
- **Utilities**: These support functions are used throughout the system for data conversion, visualization, sorting, and logging.

Together, these modules enable the analysis of chess games to identify and document strategic differences across player skill levels, ultimately generating educational and challenging chess puzzles.
```
