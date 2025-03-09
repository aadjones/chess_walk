import json
import os

from src.puzzle_bank import add_puzzle, save_bank


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


def test_puzzle_bank_operations(tmp_path):
    """
    Test multiple puzzle bank operations in sequence to ensure they work together.
    This test is designed to be less brittle by focusing on qualitative results.
    """
    # Setup test file
    file = tmp_path / "test_puzzles.json"

    # Test 1: Add first puzzle
    puzzle1 = {"fen": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR", "base_top_move": "e2e4", "difficulty": 1200}
    add_puzzle(puzzle1, file)

    # Verify first addition
    with open(file, "r") as f:
        data = json.load(f)
    assert len(data) == 1
    assert "fen" in data[0]
    assert "base_top_move" in data[0]

    # Test 2: Add second puzzle
    puzzle2 = {"fen": "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR", "base_top_move": "g1f3", "difficulty": 1300}
    add_puzzle(puzzle2, file)

    # Verify second addition
    with open(file, "r") as f:
        data = json.load(f)
    assert len(data) == 2
    assert any(p["base_top_move"] == "e2e4" for p in data)
    assert any(p["base_top_move"] == "g1f3" for p in data)

    # Test 3: Overwrite with save_bank
    new_puzzles = [
        {"fen": "new_position1", "comments": "First position"},
        {"fen": "new_position2", "comments": "Second position"},
        {"fen": "new_position3", "comments": "Third position"},
    ]
    save_bank(new_puzzles, file)

    # Verify overwrite
    with open(file, "r") as f:
        data = json.load(f)
    assert len(data) == 3
    assert all("comments" in p for p in data)
    assert not any("base_top_move" in p for p in data)  # Old data should be gone

    # Test 4: Make sure directory creation works
    nested_path = tmp_path / "sub" / "dir" / "puzzles.json"
    add_puzzle({"fen": "test_nested", "move": "a2a4"}, nested_path)
    assert os.path.exists(nested_path)

    # Verify nested file content
    with open(nested_path, "r") as f:
        data = json.load(f)
    assert len(data) == 1
    assert data[0]["move"] == "a2a4"
