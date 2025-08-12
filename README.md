# Chess Walk

Take a random walk through the mind of a particular rating band of Lichess player. Compare the results
to a stronger player. Gain insights?

## Installation

Clone the repository:

```bash
git clone https://github.com/aadjones/chess_walk.git
cd chess_walk
```

Set up a virtual environment:

```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Edit the parameters in `parameters.py` to taste.

Then, from the project root, run

```python
python scripts/generate_puzzles.py --num_walks 3
```

This will take 3 walks to scrape puzzles. It then builds the file output/puzzles.csv.

Next, to visualize the results, from the project root, run

```bash
streamlit run ui/streamlit_app.py
```

This will build a data visualization based on the data scraped from your `generate_puzzles.py` script.

## Development

To run tests, from the project root, run

```bash
pytest
```

## License

MIT
