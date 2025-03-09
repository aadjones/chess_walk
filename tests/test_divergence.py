from unittest.mock import patch
from src.divergence import find_divergence

def test_find_divergence():
    base_moves = [("e2e4", 0.6), ("g1f3", 0.3)]
    target_moves = [("g1f3", 0.8), ("e2e4", 0.1)]
    with patch("src.divergence.get_move_stats") as mock_stats:
        mock_stats.side_effect = [(base_moves, 1000), (target_moves, 1000)]
        result = find_divergence("fake_fen", "1400-1600", "1800-2000")
        assert result["base_top_move"] == "e2e4"
        assert result["target_top_move"] == "g1f3"
        assert result["target_freq"] - result["base_freq"] >= 0.5