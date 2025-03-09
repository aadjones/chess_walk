from unittest.mock import patch
from src.divergence import find_divergence
import sys
sys.path.append("..")  # Add parent directory to path
from parameters import MIN_GAMES, DIVERGENCE_THRESHOLD

def test_find_divergence():
    base_moves = [("e2e4", 0.6), ("g1f3", 0.3)]
    target_moves = [("g1f3", 0.8), ("e2e4", 0.1)]
    with patch("src.divergence.get_move_stats") as mock_stats:
        mock_stats.side_effect = [(base_moves, 1000), (target_moves, 1000)]
        result = find_divergence("fake_fen", "1400-1600", "1800-2000")
        assert result["base_top_moves"][0] == "e2e4"
        assert result["target_top_moves"][0] == "g1f3"
        assert result["target_freqs"][0] - result["base_freqs"][0] >= DIVERGENCE_THRESHOLD

def test_find_divergence_different_top_moves():
    # Test when top moves are different and frequency difference exceeds threshold
    base_moves = [("e2e4", 0.6), ("g1f3", 0.3)]
    target_moves = [("g1f3", 0.8), ("e2e4", 0.1)]
    
    with patch("src.divergence.get_move_stats") as mock_stats:
        mock_stats.side_effect = [(base_moves, 1000), (target_moves, 1000)]
        result = find_divergence("fake_fen", "1400-1600", "1800-2000")
        
        assert result["base_top_moves"][0] == "e2e4"
        assert result["target_top_moves"][0] == "g1f3"
        assert result["target_freqs"][0] - result["base_freqs"][0] >= DIVERGENCE_THRESHOLD
        assert result["fen"] == "fake_fen"
        
        # Check that the arrays contain all moves
        assert "e2e4" in result["base_top_moves"]
        assert "g1f3" in result["base_top_moves"]
        assert "e2e4" in result["target_top_moves"]
        assert "g1f3" in result["target_top_moves"]

def test_find_divergence_same_top_move():
    # Test when top moves are the same - should return None
    base_moves = [("e2e4", 0.6), ("g1f3", 0.3)]
    target_moves = [("e2e4", 0.7), ("g1f3", 0.2)]
    
    with patch("src.divergence.get_move_stats") as mock_stats:
        mock_stats.side_effect = [(base_moves, 1000), (target_moves, 1000)]
        result = find_divergence("fake_fen", "1400-1600", "1800-2000")
        
        assert result is None

def test_find_divergence_below_threshold():
    # Test when difference is below threshold - should return None
    base_moves = [("e2e4", 0.6), ("g1f3", 0.3)]
    target_moves = [("g1f3", 0.7), ("e2e4", 0.2)]  # Difference 0.1 which is below threshold
    
    with patch("src.divergence.get_move_stats") as mock_stats:
        mock_stats.side_effect = [(base_moves, 1000), (target_moves, 1000)]
        result = find_divergence("fake_fen", "1400-1600", "1800-2000")
        
        assert result is None or result["target_freqs"][0] - result["base_freqs"][0] >= DIVERGENCE_THRESHOLD

def test_find_divergence_insufficient_games():
    # Test when there aren't enough games - should return None
    base_moves = [("e2e4", 0.6), ("g1f3", 0.3)]
    target_moves = [("g1f3", 0.8), ("e2e4", 0.1)]
    
    with patch("src.divergence.get_move_stats") as mock_stats:
        mock_stats.side_effect = [(base_moves, MIN_GAMES - 1), (target_moves, 1000)]
        result = find_divergence("fake_fen", "1400-1600", "1800-2000")
        
        assert result is None

def test_find_divergence_missing_data():
    # Test when move data is missing - should return None
    with patch("src.divergence.get_move_stats") as mock_stats:
        mock_stats.side_effect = [([], 0), ([], 0)]
        result = find_divergence("fake_fen", "1400-1600", "1800-2000")
        
        assert result is None