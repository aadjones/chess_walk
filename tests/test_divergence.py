from parameters import DIVERGENCE_THRESHOLD, MIN_GAMES
import sys
from unittest.mock import patch

from src.divergence import find_divergence

sys.path.append("..")  # Add parent directory to path

# Define default move lists as dictionaries for use in multiple tests
DEFAULT_BASE_MOVES = [
    {"uci": "e2e4", "freq": 0.6, "win_rate": 0.5, "draw_rate": 0.3, "loss_rate": 0.2},
    {"uci": "g1f3", "freq": 0.3, "win_rate": 0.5, "draw_rate": 0.3, "loss_rate": 0.2},
]
DEFAULT_TARGET_MOVES = [
    {"uci": "g1f3", "freq": 0.8, "win_rate": 0.5, "draw_rate": 0.3, "loss_rate": 0.2},
    {"uci": "e2e4", "freq": 0.1, "win_rate": 0.5, "draw_rate": 0.3, "loss_rate": 0.2},
]

def test_find_divergence():
    with patch("src.divergence.get_move_stats") as mock_stats:
        mock_stats.side_effect = [(DEFAULT_BASE_MOVES, 1000), (DEFAULT_TARGET_MOVES, 1000)]
        result = find_divergence("fake_fen", "1400-1600", "1800-2000")
        assert result is not None
        # Verify that the top moves are correctly determined
        assert result["base_top_moves"][0] == "e2e4"
        assert result["target_top_moves"][0] == "g1f3"
        # Calculate the frequency difference for the top base move
        diff = DEFAULT_BASE_MOVES[0]["freq"] - next((m["freq"] for m in DEFAULT_TARGET_MOVES if m["uci"] == "e2e4"), 0)
        assert diff >= DIVERGENCE_THRESHOLD

def test_find_divergence_different_top_moves():
    with patch("src.divergence.get_move_stats") as mock_stats:
        mock_stats.side_effect = [(DEFAULT_BASE_MOVES, 1000), (DEFAULT_TARGET_MOVES, 1000)]
        result = find_divergence("fake_fen", "1400-1600", "1800-2000")
        assert result is not None
        assert result["base_top_moves"][0] == "e2e4"
        assert result["target_top_moves"][0] == "g1f3"
        assert result["fen"] == "fake_fen"
        # Check that all moves appear in the arrays
        assert "e2e4" in result["base_top_moves"]
        assert "g1f3" in result["base_top_moves"]
        assert "e2e4" in result["target_top_moves"]
        assert "g1f3" in result["target_top_moves"]

def test_find_divergence_same_top_move():
    # When both ratings yield the same top move, the function should return None
    same_moves = [
        {"uci": "e2e4", "freq": 0.6, "win_rate": 0.5, "draw_rate": 0.3, "loss_rate": 0.2},
        {"uci": "g1f3", "freq": 0.3, "win_rate": 0.5, "draw_rate": 0.3, "loss_rate": 0.2},
    ]
    with patch("src.divergence.get_move_stats") as mock_stats:
        mock_stats.side_effect = [(same_moves, 1000), (same_moves, 1000)]
        result = find_divergence("fake_fen", "1400-1600", "1800-2000")
        assert result is None

def test_find_divergence_below_threshold():
    # Using a small epsilon so the frequency difference is just below the threshold.
    epsilon = 0.01

    # Base move data: "e2e4" is the top move with frequency 0.6.
    base_moves = [
        {"uci": "e2e4", "freq": 0.6, "win_rate": 0.5, "draw_rate": 0.3, "loss_rate": 0.2},
        {"uci": "g1f3", "freq": 0.3, "win_rate": 0.5, "draw_rate": 0.3, "loss_rate": 0.2},
    ]

    # Calculate the target frequency for "e2e4" such that the difference is (DIVERGENCE_THRESHOLD - epsilon).
    target_e2e4_freq = 0.6 - (DIVERGENCE_THRESHOLD - epsilon)
    # Ensure that the top target move is different, e.g. "g1f3" has a frequency higher than target_e2e4_freq.
    target_moves = [
        {"uci": "g1f3", "freq": 0.7, "win_rate": 0.5, "draw_rate": 0.3, "loss_rate": 0.2},
        {"uci": "e2e4", "freq": target_e2e4_freq, "win_rate": 0.5, "draw_rate": 0.3, "loss_rate": 0.2},
    ]

    with patch("src.divergence.get_move_stats") as mock_stats:
        # Both rating bands have sufficient game counts.
        mock_stats.side_effect = [(base_moves, 1000), (target_moves, 1000)]
        result = find_divergence("fake_fen", "1400-1600", "1800-2000")
        # Since the frequency difference is below the threshold, we expect no divergence to be found.
        assert result is None

def test_find_divergence_insufficient_games():
    # Test when there are not enough games for the base rating - should return None
    with patch("src.divergence.get_move_stats") as mock_stats:
        mock_stats.side_effect = [(DEFAULT_BASE_MOVES, MIN_GAMES - 1), (DEFAULT_TARGET_MOVES, 1000)]
        result = find_divergence("fake_fen", "1400-1600", "1800-2000")
        assert result is None

def test_find_divergence_missing_data():
    # Test when move data is missing for both rating bands - should return None
    with patch("src.divergence.get_move_stats") as mock_stats:
        mock_stats.side_effect = [(None, 0), (None, 0)]
        result = find_divergence("fake_fen", "1400-1600", "1800-2000")
        assert result is None