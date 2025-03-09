import unittest
from unittest.mock import patch, MagicMock
import chess
import sys
import random

# Add the project root to path
sys.path.append("..")

from src.walker import random_walk, apply_move

class TestWalker(unittest.TestCase):
    
    def test_apply_move(self):
        """Test that apply_move correctly applies a chess move to a position."""
        # Starting position
        start_fen = chess.Board().fen()
        
        # Apply e4 move
        move = "e2e4"
        result_fen = apply_move(start_fen, move)
        
        # Create a board with the expected position after e4
        expected_board = chess.Board()
        expected_board.push_uci(move)
        expected_fen = expected_board.fen()
        
        self.assertEqual(result_fen, expected_fen)
    
    def test_apply_move_invalid(self):
        """Test that apply_move handles invalid moves gracefully."""
        start_fen = chess.Board().fen()
        
        # Invalid move
        invalid_move = "e2e5"  # Pawn can't move two squares diagonally
        result_fen = apply_move(start_fen, invalid_move)
        
        # Should return the original FEN
        self.assertEqual(result_fen, start_fen)
    
    @patch('src.walker.get_move_stats')
    @patch('src.walker.random.choices')
    def test_random_walk_basic(self, mock_choices, mock_get_stats):
        """Test the basic behavior of random_walk with mocked randomness."""
        # Set up mocks
        mock_get_stats.return_value = ([("e2e4", 40), ("d2d4", 30), ("g1f3", 20), ("c2c4", 10)], 100)
        mock_choices.return_value = ["e2e4"]  # Always choose e4
        
        # Call random_walk with fixed target_ply
        result = random_walk("1600", target_ply=1)
        
        # Verify the result is not None
        self.assertIsNotNone(result)
        
        # Verify a move was actually made (the FEN changed)
        start_fen = chess.Board().fen()
        self.assertNotEqual(result, start_fen)
        
        # Verify mock was called correctly
        mock_get_stats.assert_called_once()
        mock_choices.assert_called_once()
    
    @patch('src.walker.get_move_stats')
    def test_random_walk_insufficient_data(self, mock_get_stats):
        """Test that random_walk returns None when there's insufficient data."""
        # Mock get_move_stats to return insufficient data
        mock_get_stats.return_value = ([], 0)
        
        # Call random_walk
        result = random_walk("1600", target_ply=5)
        
        # Verify result is None due to insufficient data
        self.assertIsNone(result)
    
    @patch('src.walker.random.randint')
    @patch('src.walker.get_move_stats')
    @patch('src.walker.random.choices')
    def test_random_walk_target_ply_none(self, mock_choices, mock_get_stats, mock_randint):
        """Test random_walk with None target_ply (should use random value)."""
        # Set up mocks
        mock_randint.return_value = 3  # Random ply will be 3
        mock_get_stats.return_value = ([("e2e4", 40), ("d2d4", 30), ("g1f3", 20), ("c2c4", 10)], 100)
        mock_choices.return_value = ["e2e4"]  # Always choose e4
        
        # Call random_walk with None target_ply
        result = random_walk("1600", target_ply=None)
        
        # Verify the result is not None
        self.assertIsNotNone(result)
        
        # Verify random.randint was called to determine target_ply
        mock_randint.assert_called_once()
        
        # Verify get_move_stats was called the expected number of times
        self.assertEqual(mock_get_stats.call_count, 3)

if __name__ == '__main__':
    unittest.main()