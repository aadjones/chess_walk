import pandas as pd
from scipy.stats import chi2_contingency
from statsmodels.stats.proportion import proportions_ztest

from parameters import MIN_GAMES, MIN_WIN_RATE_DELTA
from src.api import get_move_stats
from src.logger import logger


def build_move_df(moves: list) -> pd.DataFrame:
    """
    Convert raw move data into a DataFrame.
    Args:
        moves (list): A list of dictionaries containing move data.

    Returns:
        pd.DataFrame: A DataFrame with the move data.
    """
    return pd.DataFrame(
        [
            {
                "Move": move["uci"],
                "Games": move["games_total"],
                "White %": move["win_rate"] * 100,
                "Draw %": move["draw_rate"] * 100,
                "Black %": move["loss_rate"] * 100,
                "Freq": move["freq"],
            }
            for move in moves
        ]
    )


def check_frequency_divergence(
    base_df: pd.DataFrame, target_df: pd.DataFrame, p_threshold: float = 0.10
) -> tuple[bool, float]:
    """
    Perform chi-square test to check if move frequencies differ significantly.
    Args:
        base_df (pd.DataFrame): The base cohort move data.
        target_df (pd.DataFrame): The target cohort move data.
        p_threshold (float): The significance level for the chi-square test.

    Returns: tuple[bool, float]: A tuple containing a boolean indicating if there is a significant difference in move frequencies and the p-value of the chi-square test.
    """
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


def check_win_rate_difference(
    base_df: pd.DataFrame, target_df: pd.DataFrame, move: str, p_threshold: float = 0.10, min_games: int = 5
) -> tuple[bool, float]:
    """
    Perform Z-test to check if win rate for a move differs significantly.
    Args:
        base_df (pd.DataFrame): The base cohort move data.
        target_df (pd.DataFrame): The target cohort move data.
        move (str): The move to check.
        p_threshold (float): The significance level for the Z-test.
        min_games (int): The minimum number of games to consider a move.

    Returns: tuple[bool, float]: A tuple containing a boolean indicating if the target move outperforms the base move and the p-value of the Z-test.
    """
    base_row = base_df[base_df["Move"] == move].iloc[0] if move in base_df["Move"].values else None
    target_row = target_df[target_df["Move"] == move].iloc[0] if move in target_df["Move"].values else None
    if base_row is None or target_row is None or base_row["Games"] < min_games or target_row["Games"] < min_games:
        return False, None
    base_wins = base_row["White %"] * base_row["Games"] / 100
    target_wins = target_row["White %"] * target_row["Games"] / 100
    count = [base_wins, target_wins]
    nobs = [base_row["Games"], target_row["Games"]]
    stat, p_value = proportions_ztest(count, nobs, alternative="two-sided")
    target_better = p_value < p_threshold and target_row["White %"] > base_row["White %"]
    return target_better, p_value


def find_divergence(fen: str, base_rating: str, target_rating: str, p_threshold: float = 0.10) -> dict | None:
    """
    Find positions where the target cohort’s top move outperforms the base cohort’s top move when played by the base cohort.
    Args:
        fen (str): The FEN of the position.
        base_rating (str): The base rating.
        target_rating (str): The target rating.
        p_threshold (float): The significance level for the Z-test.

    Returns: dict | None: A dictionary containing the divergence information if a divergence is detected, otherwise None.
    """
    logger.info(f"Analyzing position for divergence between ratings {base_rating} and {target_rating}")
    logger.debug(f"Position: {fen}")
    base_moves, base_total = get_move_stats(fen, base_rating)
    target_moves, target_total = get_move_stats(fen, target_rating)
    if not base_moves or not target_moves:
        logger.warning(f"No moves data for {fen} at rating {base_rating if not base_moves else target_rating}")
        return None
    if base_total < MIN_GAMES or target_total < MIN_GAMES:
        logger.warning(f"Insufficient games: base={base_total}, target={target_total}, min required={MIN_GAMES}")
        return None
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
    # Compare target move’s win rate to base’s top move win rate in base cohort
    base_top_win = base_df.iloc[0]["White %"]
    base_win = (
        base_df[base_df["Move"] == top_target_move]["White %"].iloc[0]
        if top_target_move in base_df["Move"].values
        else 0
    )
    base_games = (
        base_df[base_df["Move"] == top_target_move]["Games"].iloc[0] if top_target_move in base_df["Move"].values else 0
    )
    target_win = target_df[target_df["Move"] == top_target_move]["White %"].iloc[0]  # For logging only
    if base_win - base_top_win >= MIN_WIN_RATE_DELTA and base_games >= 5:  # Target move beats base’s top move in base cohort
        logger.info(
            f"Base cohort win rate for top move {top_base_move}: {base_top_win:.2f}%, "
            f"Base cohort win rate for {top_target_move}: {base_win:.2f}% (games: {base_games}), "
            f"Target cohort win rate: {target_win:.2f}%"
        )
        logger.info(f"Divergence detected! Target prefers {top_target_move}, outperforms base top move")
        return {
            "fen": fen,
            "base_rating": base_rating,
            "target_rating": target_rating,
            "base_df": base_df,
            "target_df": target_df,
            "top_base_move": top_base_move,
            "top_target_move": top_target_move,
            "p_freq": p_freq,
            "base_win_for_target_move": base_win,
            "base_win_for_top_move": base_top_win,
        }
    logger.info(
        f"Target move {top_target_move} not better than base top move {top_base_move}: "
        f"base win rate={base_win:.2f}%, base top win rate={base_top_win:.2f}%, games={base_games}"
    )
    return None
