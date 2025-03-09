from src.puzzle_bank import add_puzzle, save_bank
import json

def test_add_puzzle(tmp_path):
    puzzle = {"fen": "fake_fen", "base_top_move": "e2e4"}
    file = tmp_path / "puzzles.json"
    add_puzzle(puzzle, file)
    with open(file, "r") as f:
        data = json.load(f)
    assert len(data) == 1
    assert data[0]["fen"] == "fake_fen"

def test_save_bank(tmp_path):
    puzzles = [{"fen": "fake_fen"}]
    file = tmp_path / "puzzles.json"
    save_bank(puzzles, file)
    with open(file, "r") as f:
        data = json.load(f)
    assert data == puzzles