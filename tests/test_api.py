from unittest.mock import patch
from src.api import get_move_stats

def test_get_move_stats():
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
        moves, total = get_move_stats("fake_fen", "1400-1600")
        assert moves == [("e2e4", 0.68), ("e2e3", 0.16)]  # 1000/1250, 200/1250
        assert total == 1250