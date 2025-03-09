import urllib.parse
from unittest.mock import patch

import requests

from parameters import RATE_LIMIT_DELAY
from src.api import get_move_stats

# Define a constant for the valid FEN string
VALID_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

def test_get_move_stats_success():
    """Test successful API call with standard response"""
    mock_response = {
        "moves": [
            {"uci": "e2e4", "white": 500, "black": 300, "draws": 200},
            {"uci": "e2e3", "white": 100, "black": 50, "draws": 50},
        ],
        "white": 600,
        "black": 350,
        "draws": 250,
    }
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.status_code = 200

        moves, total = get_move_stats(VALID_FEN, "1400-1600")

        # Verify move calculations
        assert moves[0]["uci"] == "e2e4"
        assert round(moves[0]["freq"], 2) == 0.83  # (500+300+200)/1200 = 0.83
        assert moves[1]["uci"] == "e2e3"
        assert round(moves[1]["freq"], 2) == 0.17  # (100+50+50)/1200 = 0.17
        assert total == 1200

        # Verify the API call
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        params = kwargs.get("params", {})
        assert "ratings" in params and params["ratings"] == "1400,1600"

def test_get_move_stats_comma_rating():
    """Test handling of comma-separated rating format"""
    mock_response = {
        "moves": [{"uci": "e2e4", "white": 100, "black": 50, "draws": 50}],
        "white": 100,
        "black": 50,
        "draws": 50,
    }

    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.status_code = 200

        moves, total = get_move_stats(VALID_FEN, "1400,1600")

        # Verify API was called with correct rating format
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        params = kwargs.get("params", {})
        assert "ratings" in params and params["ratings"] == "1400,1600"

def test_get_move_stats_http_error():
    """Test handling of HTTP errors"""
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 404
        mock_get.return_value.text = "Not Found"

        moves, total = get_move_stats(VALID_FEN, "1400-1600")

        assert moves is None
        assert total == 0

def test_get_move_stats_request_exception():
    """Test handling of request exceptions"""
    with patch("requests.get") as mock_get:
        mock_get.side_effect = requests.RequestException("Connection error")

        moves, total = get_move_stats(VALID_FEN, "1400-1600")

        assert moves is None
        assert total == 0

def test_get_move_stats_json_error():
    """Test handling of JSON parsing errors"""
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.side_effect = ValueError("Invalid JSON")

        moves, total = get_move_stats(VALID_FEN, "1400-1600")

        assert moves is None
        assert total == 0

def test_get_move_stats_empty_response():
    """Test handling of valid response with no moves"""
    mock_response = {"moves": [], "white": 0, "black": 0, "draws": 0}

    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.status_code = 200

        moves, total = get_move_stats(VALID_FEN, "1400-1600")

        assert moves is None
        assert total == 0

def test_get_move_stats_no_games():
    """Test handling of valid response but zero games"""
    mock_response = {"moves": [{"uci": "e2e4", "white": 0, "black": 0, "draws": 0}], "white": 0, "black": 0, "draws": 0}

    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.status_code = 200

        moves, total = get_move_stats(VALID_FEN, "1400-1600")

        assert moves is None
        assert total == 0

def test_get_move_stats_rate_limit():
    """Test that rate limiting delay is applied"""
    mock_response = {
        "moves": [{"uci": "e2e4", "white": 100, "black": 0, "draws": 0}],
        "white": 100,
        "black": 0,
        "draws": 0,
    }

    with patch("requests.get") as mock_get, patch("time.sleep") as mock_sleep:
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.status_code = 200

        get_move_stats(VALID_FEN, "1400-1600")

        # Verify that sleep was called for rate limiting
        mock_sleep.assert_called_once_with(RATE_LIMIT_DELAY)

def test_get_move_stats_url_construction():
    """Test that the API URL is constructed correctly with proper encoding"""
    mock_response = {
        "moves": [{"uci": "e2e4", "white": 100, "black": 50, "draws": 50}],
        "white": 100,
        "black": 50,
        "draws": 50,
    }

    # Test with standard FEN string
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.status_code = 200

        # Starting position FEN
        get_move_stats(VALID_FEN, "1400-1600")

        # Verify URL construction
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        params = kwargs.get("params", {})
        assert params["variant"] == "standard"
        assert params["speeds"] == "blitz,rapid,classical"
        assert params["ratings"] == "1400,1600"
        assert params["fen"] == VALID_FEN  # FEN is passed as-is, encoding handled by requests

    # Test with a more complex FEN
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.status_code = 200

        complex_fen = "r1bqkbnr/pp1ppppp/2n5/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 1"
        get_move_stats(complex_fen, "1800,2000")

        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        params = kwargs.get("params", {})
        assert params["ratings"] == "1800,2000"