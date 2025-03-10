import pandas as pd
import pytest
from unittest.mock import patch
from src.divergence import (build_move_df, check_frequency_divergence, 
                            check_win_rate_difference, find_divergence)

# Sample move data for testing
BASE_MOVES = [
    {"uci": "f1b5", "games_total": 18337, "win_rate": 0.4341, "draw_rate": 0.0613, "loss_rate": 0.5046, "freq": 0.4528},
    {"uci": "f1e2", "games_total": 12013, "win_rate": 0.4724, "draw_rate": 0.0798, "loss_rate": 0.4478, "freq": 0.2966},
]
TARGET_MOVES = [
    {"uci": "f1e2", "games_total": 309, "win_rate": 0.6000, "draw_rate": 0.1000, "loss_rate": 0.3000, "freq": 0.4003},
    {"uci": "f1b5", "games_total": 267, "win_rate": 0.4419, "draw_rate": 0.1311, "loss_rate": 0.4270, "freq": 0.3459},
]

# Silence Pandas FutureWarning
pd.set_option('future.no_silent_downcasting', True)

def test_build_move_df():
    """Test that build_move_df correctly converts move data to a DataFrame."""
    df = build_move_df(BASE_MOVES)
    assert len(df) == 2
    assert df.iloc[0]["Move"] == "f1b5"
    assert df.iloc[0]["White %"] == pytest.approx(43.41, 0.01)
    assert df.iloc[1]["Freq"] == pytest.approx(0.2966, 0.0001)

def test_frequency_divergence_significant():
    """Test chi-square detects significant frequency divergence."""
    base_df = build_move_df(BASE_MOVES)
    target_df = build_move_df(TARGET_MOVES)
    differs, p_value = check_frequency_divergence(base_df, target_df)
    assert differs
    assert p_value < 0.05

def test_frequency_divergence_insignificant():
    """Test chi-square detects no significant frequency divergence."""
    same_moves = [
        {"uci": "f1b5", "games_total": 100, "win_rate": 0.5, "draw_rate": 0.3, "loss_rate": 0.2, "freq": 0.5},
        {"uci": "f1e2", "games_total": 100, "win_rate": 0.5, "draw_rate": 0.3, "loss_rate": 0.2, "freq": 0.5},
    ]
    base_df = build_move_df(same_moves)
    target_df = build_move_df(same_moves)
    differs, p_value = check_frequency_divergence(base_df, target_df)
    assert not differs
    assert p_value >= 0.05

def test_win_rate_difference_significant():
    """Test Z-test detects significant win rate difference."""
    base_df = pd.DataFrame({"Move": ["f1e2"], "Games": [1000], "White %": [40.0]})
    target_df = pd.DataFrame({"Move": ["f1e2"], "Games": [1000], "White %": [50.0]})
    better, p_value = check_win_rate_difference(base_df, target_df, "f1e2")
    assert better
    assert p_value < 0.05

def test_win_rate_difference_insignificant():
    """Test Z-test detects no significant win rate difference."""
    # Use a small, insignificant difference
    base_df = pd.DataFrame({"Move": ["f1e2"], "Games": [1000], "White %": [47.0]})
    target_df = pd.DataFrame({"Move": ["f1e2"], "Games": [1000], "White %": [48.0]})
    better, p_value = check_win_rate_difference(base_df, target_df, "f1e2")
    assert not better
    assert p_value > 0.05

def test_win_rate_difference_insufficient_data():
    """Test Z-test handles insufficient data."""
    base_df = pd.DataFrame({"Move": ["f1e2"], "Games": [2], "White %": [50.0]})
    target_df = pd.DataFrame({"Move": ["f1e2"], "Games": [100], "White %": [60.0]})
    better, p_value = check_win_rate_difference(base_df, target_df, "f1e2")
    assert not better
    assert p_value is None

@pytest.mark.usefixtures("caplog")
def test_find_divergence_significant(caplog):
    """Test find_divergence detects significant divergence."""
    with patch('src.divergence.get_move_stats') as mock_get_move_stats:
        mock_get_move_stats.side_effect = [
            (BASE_MOVES, sum(m["games_total"] for m in BASE_MOVES)),
            (TARGET_MOVES, sum(m["games_total"] for m in TARGET_MOVES))
        ]
        caplog.set_level("INFO")
        result = find_divergence("test_fen", "2000", "2500", p_threshold=0.10)
        assert result is not None
        assert result["top_base_move"] == "f1b5"
        assert result["top_target_move"] == "f1e2"
        assert result["p_freq"] < 0.05
        assert "Divergence confirmed" in caplog.text

@pytest.mark.usefixtures("caplog")
def test_find_divergence_no_divergence(caplog):
    """Test find_divergence returns None when frequencies don’t differ."""
    with patch('src.divergence.get_move_stats') as mock_get_move_stats:
        same_moves = [
            {"uci": "f1b5", "games_total": 100, "win_rate": 0.5, "draw_rate": 0.3, "loss_rate": 0.2, "freq": 0.5},
            {"uci": "f1e2", "games_total": 50, "win_rate": 0.5, "draw_rate": 0.3, "loss_rate": 0.2, "freq": 0.25},
        ]
        mock_get_move_stats.side_effect = [
            (same_moves, sum(m["games_total"] for m in same_moves)),
            (same_moves, sum(m["games_total"] for m in same_moves))
        ]
        caplog.set_level("INFO")
        result = find_divergence("test_fen", "2000", "2500")
        assert result is None
        assert "No significant frequency divergence" in caplog.text

@pytest.mark.usefixtures("caplog")
def test_find_divergence_insufficient_games(caplog):
    """Test find_divergence handles insufficient games."""
    with patch('src.divergence.get_move_stats') as mock_get_move_stats:
        mock_get_move_stats.side_effect = [
            (BASE_MOVES, 1),  # Below MIN_GAMES
            (TARGET_MOVES, sum(m["games_total"] for m in TARGET_MOVES))
        ]
        caplog.set_level("INFO")
        result = find_divergence("test_fen", "2000", "2500")
        assert result is None
        assert "Insufficient games" in caplog.text

@pytest.mark.usefixtures("caplog")
def test_find_divergence_no_data(caplog):
    """Test find_divergence handles no move data."""
    with patch('src.divergence.get_move_stats') as mock_get_move_stats:
        mock_get_move_stats.side_effect = [(None, 0), (TARGET_MOVES, sum(m["games_total"] for m in TARGET_MOVES))]
        caplog.set_level("INFO")
        result = find_divergence("test_fen", "2000", "2500")
        assert result is None
        assert "No moves data" in caplog.text