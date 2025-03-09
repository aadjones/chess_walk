# Chess Walk

Take a random walk through the mind of a particular rating band of Lichess player. Compare the results
to a stronger player. Gain insights!

## Installation

Clone the repository:

```bash
git clone https://github.com/aadjones/chess_walk.git
cd chess_walk
```

Set up a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Edit the parameters in ```parameters.py``` to taste.

Then, from the project root, run

```python
python main.py --num_walks 5
```

This will take 5 walks to scrape puzzles. It then builds the file output/puzzles.json as well as the website output/puzzles.html. View the site with a local server to browse through the puzzles.

## Development

To run tests, from the project root, run

```bash
pytest
```

## License

MIT
