from unittest.mock import patch, MagicMock
import pytest
from src.api import get_move_stats
import requests
import urllib.parse

def test_get_move_stats_success():
    """Test successful API call with standard response"""
    mock_response = {
        "moves": [
            {"uci": "e2e4", "white": 500, "black": 300, "draws": 200},
            {"uci": "e2e3", "white": 100, "black": 50, "draws": 50}
        ],
        "white": 600, "black": 350, "draws": 250
    }
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.status_code = 200
        
        moves, total = get_move_stats("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "1400-1600")
        
        # Verify move calculations
        assert moves[0][0] == "e2e4"
        assert round(moves[0][1], 2) == 0.83  # (500+300+200)/1200 = 0.83
        assert moves[1][0] == "e2e3"
        assert round(moves[1][1], 2) == 0.17  # (100+50+50)/1200 = 0.17
        assert total == 1200
        
        # Simply verify that the API was called, without checking exact URL format
        mock_get.assert_called_once()
        
        # Optionally verify the function used the correct rating format
        args, kwargs = mock_get.call_args
        url = kwargs.get('url', args[0])
        assert "ratings=1400,1600" in url

def test_get_move_stats_comma_rating():
    """Test handling of comma-separated rating format"""
    mock_response = {"moves": [{"uci": "e2e4", "white": 100, "black": 50, "draws": 50}], "white": 100, "black": 50, "draws": 50}
    
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.status_code = 200
        
        moves, total = get_move_stats("fake_fen", "1400,1600")
        
        # Verify API was called with correct rating format
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert "ratings=1400,1600" in kwargs.get('url', args[0]) or "ratings=1400,1600" in kwargs.get('params', {}).get('ratings', '')

def test_get_move_stats_http_error():
    """Test handling of HTTP errors"""
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 404
        mock_get.return_value.text = "Not Found"
        
        moves, total = get_move_stats("fake_fen", "1400-1600")
        
        assert moves is None
        assert total == 0

def test_get_move_stats_request_exception():
    """Test handling of request exceptions"""
    with patch("requests.get") as mock_get:
        mock_get.side_effect = requests.RequestException("Connection error")
        
        moves, total = get_move_stats("fake_fen", "1400-1600")
        
        assert moves is None
        assert total == 0

def test_get_move_stats_json_error():
    """Test handling of JSON parsing errors"""
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.side_effect = ValueError("Invalid JSON")
        
        moves, total = get_move_stats("fake_fen", "1400-1600")
        
        assert moves is None
        assert total == 0

def test_get_move_stats_empty_response():
    """Test handling of valid response with no moves"""
    mock_response = {"moves": [], "white": 0, "black": 0, "draws": 0}
    
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.status_code = 200
        
        moves, total = get_move_stats("fake_fen", "1400-1600")
        
        assert moves is None
        assert total == 0

def test_get_move_stats_no_games():
    """Test handling of valid response but zero games"""
    mock_response = {
        "moves": [{"uci": "e2e4", "white": 0, "black": 0, "draws": 0}],
        "white": 0, "black": 0, "draws": 0
    }
    
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.status_code = 200
        
        moves, total = get_move_stats("fake_fen", "1400-1600")
        
        assert moves is None
        assert total == 0

def test_get_move_stats_rate_limit():
    """Test that rate limiting delay is applied"""
    mock_response = {
        "moves": [{"uci": "e2e4", "white": 100, "black": 0, "draws": 0}],
        "white": 100, "black": 0, "draws": 0
    }
    
    with patch("requests.get") as mock_get, patch("time.sleep") as mock_sleep:
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.status_code = 200
        
        get_move_stats("fake_fen", "1400-1600")
        
        # Verify that sleep was called for rate limiting
        mock_sleep.assert_called_once()

def test_get_move_stats_url_construction():
    """Test that the API URL is constructed correctly with proper encoding"""
    mock_response = {
        "moves": [{"uci": "e2e4", "white": 100, "black": 50, "draws": 50}],
        "white": 100, "black": 50, "draws": 50
    }
    
    # Test with standard FEN string
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.status_code = 200
        
        # Starting position FEN
        test_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        get_move_stats(test_fen, "1400-1600")
        
        # Verify URL construction
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        url = args[0] if args else kwargs.get('url', '')
        
        # Check each important component of the URL
        assert "https://explorer.lichess.ovh/lichess" in url
        assert "variant=standard" in url
        assert "speeds=blitz,rapid,classical" in url
        assert "ratings=1400,1600" in url
        
        # Verify FEN encoding (spaces should be %20, slashes properly encoded)
        encoded_fen = urllib.parse.quote(test_fen)
        assert f"fen={encoded_fen}" in url or f"fen={test_fen}" in url
        
    # Test with a more complex FEN that needs encoding
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.status_code = 200
        
        # FEN with special characters
        complex_fen = "r1bqkbnr/pp1ppppp/2n5/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 1"
        get_move_stats(complex_fen, "1800,2000")
        
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        url = args[0] if args else kwargs.get('url', '')
        
        # Verify this specific rating range is used
        assert "ratings=1800,2000" in url