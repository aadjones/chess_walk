# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Chess Walk is a Python application that analyzes chess positions by comparing move preferences between different rating bands of Lichess players. It identifies positions where stronger players prefer different moves than weaker players, then provides a Streamlit UI for exploration.

### Core Principles

- **Data Quality > Statistical Sophistication:** Trust real Lichess game data over complex models.
- **Clear Divergence > Marginal Differences:** Only surface positions with meaningful rating-based variations.
- **Working Analysis > Perfect UI:** Focus on accurate chess position analysis before polishing visualization.
- **Simple Statistics > Advanced Models:** Use chi-square and z-tests that are interpretable over black-box methods.
- **Real Games > Theoretical Positions:** Ground all analysis in actual player behavior from Lichess database.

### Default Questions to Ask (Yourself and the User)

- Is this divergence actually meaningful to chess understanding, or just statistical noise?
- Are we analyzing enough games to make this conclusion reliable?
- Does this position actually teach something about rating differences?
- Can we validate this finding against chess principles or master analysis?

## Development Commands

### Environment Setup
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Testing
```bash
pytest                    # Run all tests
pytest tests/test_*.py    # Run specific test file
```

### Code Quality
```bash
black .                   # Format code (line-length=120)
isort .                   # Sort imports
flake8 .                  # Lint code
```

### Main Application Workflows
```bash
# Generate positions from chess position analysis
python scripts/generate_positions.py --num_walks 3

# Launch Streamlit UI for data visualization
streamlit run ui/streamlit_app.py

# Alternative: Use Makefile
make run                  # Runs streamlit app
make summarize           # Run summarizer module
make clean               # Clean build artifacts
```

## Architecture

### Core Data Flow
1. **Walker** (`src/walker.py`) - Performs random walks through chess positions using Lichess API data
2. **API Layer** (`src/api.py`) - Interfaces with Lichess Explorer API for move statistics
3. **Divergence Detection** (`src/divergence.py`) - Statistical analysis to find significant differences between rating bands
4. **Data Storage** - Positions saved to `output/positions.csv` with three-level index (Cohort, Row, PositionIdx)

### Key Components
- **Parameters** (`parameters.py`) - Central configuration for rating bands, API settings, and analysis thresholds
- **Chess Utils** (`src/chess_utils.py`) - Chess-specific utilities for position handling
- **Streamlit UI** (`ui/` directory) - Modular UI components for data visualization and interaction

### Rating System
The application uses discrete rating bands from Lichess API:
- Valid ratings: ["0", "1000", "1200", "1400", "1600", "1800", "2000", "2200", "2500"]
- Default comparison: BASE_RATING="2000" vs TARGET_RATING="2500"

### Statistical Analysis
- Chi-square tests for frequency divergence between rating groups
- Z-tests for win rate comparisons
- Minimum games threshold (MIN_GAMES=2) and win rate delta (MIN_WIN_RATE_DELTA=0.07)

## File Structure Patterns
- `src/` - Core business logic and API interfaces
- `ui/` - Streamlit application modules (config, data loading, display)
- `scripts/` - Entry point scripts and utilities
- `tests/` - Test files following pytest conventions
- `summarizer/` - Analysis and reporting utilities
- `output/` - Generated data files

## Testing Philosophy

Write **focused unit tests for chess analysis logic only**. Follow these principles:

### What to Test
- **Statistical calculations**: Chi-square tests, z-tests, divergence detection accuracy
- **Chess position handling**: FEN parsing, move validation, board state transitions
- **Data transformations**: API response processing, CSV generation, rating band mapping
- **Business logic**: Minimum games thresholds, win rate calculations, position filtering
- **Edge cases**: Invalid FENs, insufficient game data, API failures

### What NOT to Test
- **Streamlit UI**: Don't test user interactions, widget rendering, or display formatting
- **External APIs**: Avoid testing Lichess API responses directly (mock instead)
- **File I/O details**: Don't test CSV formatting specifics or file system operations
- **Random walks**: Don't test specific move sequences (focus on statistical properties)

### Test Quality Guidelines
- **Meaningful divergence**: Test that 2500 vs 2000 shows different patterns, not exact percentages
- **Statistical validity**: Verify p-values are reasonable, not precise decimal values
- **Chess accuracy**: Ensure moves are legal and positions make sense
- **Fast and reliable**: Tests should run without network calls or large data files

### Example Good Tests
```python
# Good: Tests meaningful behavior
assert find_divergence(fen, "2000", "2500")["p_freq"] < 0.10

# Bad: Tests exact statistics
assert base_df.iloc[0]["White %"] == 67.23
```

## Configuration
- All major parameters centralized in `parameters.py`
- Streamlit config in `ui/config.py` using Pydantic settings
- pyproject.toml contains pytest and code formatting configurations