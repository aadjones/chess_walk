import pandas as pd
from scipy.stats import chi2_contingency
from statsmodels.stats.proportion import proportions_ztest
from parameters import MIN_GAMES
from src.api import get_move_stats
from src.logger import logger

def build_move_df(moves):
    """Convert raw move data into a DataFrame."""
    return pd.DataFrame([
        {
            "Move": move["uci"],
            "Games": move["games_total"],
            "White %": move["win_rate"] * 100,
            "Draw %": move["draw_rate"] * 100,
            "Black %": move["loss_rate"] * 100,
            "Freq": move["freq"],
        }
        for move in moves
    ])

def check_frequency_divergence(base_df, target_df, p_threshold=0.05):
    """Perform chi-square test to check if move frequencies differ significantly."""
    all_moves = set(base_df["Move"]).union(set(target_df["Move"]))
    contingency = pd.DataFrame(index=list(all_moves), columns=["Base", "Target"]).fillna(0)
    for move in all_moves:
        base_games = base_df[base_df["Move"] == move]["Games"].sum() if move in base_df["Move"].values else 0
        target_games = target_df[target_df["Move"] == move]["Games"].sum() if move in target_df["Move"].values else 0
        contingency.loc[move, "Base"] = base_games
        contingency.loc[move, "Target"] = target_games
    contingency = contingency.astype(float)
    chi2, p_value, dof, expected = chi2_contingency(contingency)
    return p_value < p_threshold, p_value

def check_win_rate_difference(base_df, target_df, move, p_threshold=0.05, min_games=5):
    """Perform Z-test to check if win rate for a move differs significantly."""
    base_row = base_df[base_df["Move"] == move].iloc[0] if move in base_df["Move"].values else None
    target_row = target_df[target_df["Move"] == move].iloc[0] if move in target_df["Move"].values else None
    if (base_row is None or target_row is None or 
        base_row["Games"] < min_games or target_row["Games"] < min_games):
        return False, None
    base_wins = base_row["White %"] * base_row["Games"] / 100
    target_wins = target_row["White %"] * target_row["Games"] / 100
    count = [base_wins, target_wins]
    nobs = [base_row["Games"], target_row["Games"]]
    stat, p_value = proportions_ztest(count, nobs, alternative="two-sided")
    target_better = p_value < p_threshold and target_row["White %"] > base_row["White %"]
    return target_better, p_value

def find_divergence(fen, base_rating, target_rating, p_threshold=0.05):
    """Find positions where higher-rated players prefer a different move with a better outcome."""
    logger.info(f"Analyzing position for divergence between ratings {base_rating} and {target_rating}")
    logger.debug(f"Position: {fen}")
    base_moves, base_total = get_move_stats(fen, base_rating)
    target_moves, target_total = get_move_stats(fen, target_rating)
    if not base_moves or not target_moves:
        logger.warning(f"No moves data for {fen} at rating {base_rating if not base_moves else target_rating}")
        return None
    if base_total < MIN_GAMES or target_total < MIN_GAMES:
        logger.warning(f"Insufficient games: base={base_total}, target={target_total}, min required={MIN_GAMES}")
        return None  # This ensures early exit
    base_df = build_move_df(base_moves)
    target_df = build_move_df(target_moves)
    logger.debug(f"Base DataFrame:\n{base_df}")
    logger.debug(f"Target DataFrame:\n{target_df}")
    freq_differs, p_freq = check_frequency_divergence(base_df, target_df, p_threshold)
    logger.info(f"Chi-square p-value for frequency: {p_freq:.4f} (significant: {freq_differs})")
    if not freq_differs:
        logger.info("No significant frequency divergence")
        return None
    base_df = base_df.sort_values(by="Freq", ascending=False)
    target_df = target_df.sort_values(by="Freq", ascending=False)
    top_base_move = base_df.iloc[0]["Move"]
    top_target_move = target_df.iloc[0]["Move"]
    if top_base_move == top_target_move:
        logger.info("No divergence - same top move in both rating bands")
        return None
    target_better, p_win = check_win_rate_difference(base_df, target_df, top_target_move, p_threshold)
    logger.info(f"Z-test for {top_target_move}: p-value = {p_win if p_win is not None else 'N/A':.4f}, "
                f"Target better = {target_better}")
    if target_better:
        base_win = base_df[base_df["Move"] == top_target_move]["White %"].iloc[0]
        target_win = target_df[target_df["Move"] == top_target_move]["White %"].iloc[0]
        logger.info(f"Base win rate: {base_win:.2f}%, Target win rate: {target_win:.2f}%")
        logger.info(f"Divergence confirmed! Target prefers {top_target_move} with better outcome")
        return {
            "fen": fen,
            "base_rating": base_rating,
            "target_rating": target_rating,
            "base_df": base_df,
            "target_df": target_df,
            "top_base_move": top_base_move,
            "top_target_move": top_target_move,
            "p_freq": p_freq,
            "p_win": p_win,
        }
    logger.info("Target’s top move not significantly better")
    return None