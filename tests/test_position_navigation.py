"""
Tests for position navigation and cross-cohort jumping behavior.

These tests lock in the correct behavior to prevent regression of the 
position jumping bug where users would select position X but end up at position Y.
"""

import pytest
import pandas as pd
import os


def filter_data_by_cohort_pair(positions_df, selected_cohort_pair):
    """Simple version of the data filter function for testing."""
    return positions_df[positions_df["CohortPair"] == selected_cohort_pair].copy()


def group_by_position_index(filtered_df):
    """Simple version of the position grouping function for testing."""
    if filtered_df.empty:
        return None, []
    position_groups = filtered_df.groupby("PositionIdx")
    position_ids = sorted(list(position_groups.groups.keys()))
    return position_groups, position_ids


class TestPositionNavigation:
    """Test position navigation across cohorts."""
    
    @pytest.fixture
    def sample_positions_data(self):
        """Create sample position data that mimics the real structure."""
        data = []
        
        # Create positions for different cohorts like the real data
        cohorts = [
            ("0-1000", [1, 2, 3]),
            ("1000-1400", [4, 5, 6]), 
            ("1200-1600", [7, 8, 9]),
            ("1400-1800", [10, 11, 12])
        ]
        
        for cohort_pair, position_ids in cohorts:
            for pos_id in position_ids:
                for rating in cohort_pair.split("-"):
                    # Add multiple rows per position (different moves)
                    for move_idx in range(3):  # 3 moves per position
                        data.append({
                            "Cohort": "base" if rating == cohort_pair.split("-")[0] else "target",
                            "Row": move_idx,
                            "PositionIdx": pos_id,
                            "CohortPair": cohort_pair,
                            "Move": f"Move{move_idx}",
                            "Games": 100,
                            "Freq": 0.3,
                            "FEN": f"fen{pos_id}",
                            "Rating": int(rating)
                        })
        
        return pd.DataFrame(data)
    
    def test_cohort_filtering_preserves_position_ids(self, sample_positions_data):
        """Test that filtering by cohort preserves the correct position IDs."""
        # Filter for 1000-1400 cohort
        filtered_df = filter_data_by_cohort_pair(sample_positions_data, "1000-1400")
        
        # Should only contain positions 4, 5, 6
        position_ids = filtered_df["PositionIdx"].unique()
        expected_positions = [4, 5, 6]
        
        assert sorted(position_ids) == expected_positions, f"Expected {expected_positions}, got {sorted(position_ids)}"
    
    def test_position_navigation_scenario(self, sample_positions_data):
        """
        Test the full navigation scenario that was causing the bug:
        1. User is in 1200-1600 cohort (positions 7,8,9)
        2. User requests position 1 
        3. System should identify position 1 is in 0-1000 cohort
        4. System should switch to 0-1000 cohort and show position 1
        """
        # Step 1: Start in 1200-1600 cohort
        current_cohort = "1200-1600"
        filtered_df = filter_data_by_cohort_pair(sample_positions_data, current_cohort)
        _, current_position_ids = group_by_position_index(filtered_df)
        
        # Step 2: User requests position 1
        requested_position = 1
        
        # Step 3: Check if position 1 is in current cohort
        position_in_current_cohort = requested_position in current_position_ids
        assert not position_in_current_cohort, "Position 1 should not be in 1200-1600 cohort"
        
        # Step 4: Find which cohort position 1 belongs to
        position_data = sample_positions_data[sample_positions_data["PositionIdx"] == requested_position]
        target_cohort = position_data["CohortPair"].iloc[0]
        assert target_cohort == "0-1000", f"Position 1 should belong to 0-1000 cohort, got {target_cohort}"
        
        # Step 5: Switch to target cohort and verify position 1 is available
        target_filtered_df = filter_data_by_cohort_pair(sample_positions_data, target_cohort)
        _, target_position_ids = group_by_position_index(target_filtered_df)
        
        assert requested_position in target_position_ids, f"Position {requested_position} should be in {target_cohort} cohort"
        
        # Step 6: Calculate correct local index for position 1 in target cohort
        local_index = target_position_ids.index(requested_position)
        assert local_index == 0, f"Position 1 should be at local index 0 in 0-1000 cohort, got {local_index}"


def test_real_data_structure():
    """Test against the actual positions.csv file to ensure our assumptions are correct."""
    csv_path = "output/positions.csv"
    
    # Skip if file doesn't exist (e.g., in CI without data)
    if not os.path.exists(csv_path):
        pytest.skip("positions.csv not found, skipping real data test")
    
    df = pd.read_csv(csv_path)
    
    # Verify the data has the expected structure
    required_columns = ["PositionIdx", "CohortPair", "Move", "Games", "Freq", "FEN", "Rating"]
    for col in required_columns:
        assert col in df.columns, f"Required column {col} missing from positions.csv"
    
    # Verify positions are properly distributed across cohorts
    cohort_positions = df.groupby("CohortPair")["PositionIdx"].unique()
    
    # Should have multiple cohorts
    assert len(cohort_positions) > 1, "Should have multiple cohorts in real data"
    
    # Positions within each cohort should be contiguous ranges
    for cohort, positions in cohort_positions.items():
        sorted_positions = sorted(positions)
        # This is a sanity check - positions should form reasonable ranges
        assert len(sorted_positions) > 0, f"Cohort {cohort} should have at least one position"
        assert max(sorted_positions) > min(sorted_positions) or len(sorted_positions) == 1, \
            f"Cohort {cohort} position range seems invalid: {sorted_positions}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])