from unittest.mock import patch

import pytest

from roll_parser import (
    DiceParsingError,
    DiceResult,
    DiceRoll,
    DiceRollStats,
    parse_dice_roll,
    simulate_dice_roll,
    simulate_dice_statistics,
)


# Test valid dice roll formats
@pytest.mark.parametrize(
    "dice_string, expected",
    [
        # Basic formats
        ("2d6", DiceRoll(2, 6, 0)),
        ("1d20+5", DiceRoll(1, 20, 5)),
        ("3d8-2", DiceRoll(3, 8, -2)),
        # Whitespace handling
        (" 2 d 10 + 3 ", DiceRoll(2, 10, 3)),
        # Case insensitivity
        ("4D12", DiceRoll(4, 12, 0)),
        # Edge cases
        ("100d100+50", DiceRoll(100, 100, 50)),
        ("0d6", DiceRoll(0, 6, 0)),
        ("1d0", DiceRoll(1, 0, 0)),
        ("2d6+0", DiceRoll(2, 6, 0)),
    ],
)
def test_valid_dice_rolls(dice_string, expected):
    assert parse_dice_roll(dice_string) == expected


# Test invalid dice roll formats
@pytest.mark.parametrize(
    "invalid_dice_string",
    [
        # Invalid formats
        "invalid",
        "d20",  # Missing dice count
        "2d",  # Missing sides count
        "2d6+",  # Incomplete modifier
        "2d6++3",  # Double modifier symbol
        "2d6+3x",  # Extra characters
        "-2d6",  # Negative dice count
        "2d-6",  # Negative sides count
        "2d6d4",  # Multiple 'd' characters
        "2d6+3+2",  # Multiple modifiers
        "2.5d6",  # Decimal values
        "2d6.5",
        "2d6+1.5",
        "",  # Empty string
    ],
)
def test_invalid_dice_rolls(invalid_dice_string):
    with pytest.raises(DiceParsingError):
        parse_dice_roll(invalid_dice_string)


def test_none_input():
    """Test handling of None input."""
    with pytest.raises(AttributeError):
        parse_dice_roll(None)


# Tests for simulate_dice_roll
def test_simulate_dice_roll_basic():
    """Test basic dice roll simulation."""
    roll = DiceRoll(num_dice=2, num_sides=6, modifier=3)
    result = simulate_dice_roll(roll)

    assert isinstance(result, DiceResult)
    assert len(result.individual_values) == 2
    assert all(1 <= value <= 6 for value in result.individual_values)
    assert result.modifier == 3
    assert result.total == sum(result.individual_values) + 3


def test_simulate_dice_roll_zero_dice():
    """Test rolling zero dice."""
    roll = DiceRoll(num_dice=0, num_sides=6, modifier=5)
    result = simulate_dice_roll(roll)

    assert isinstance(result, DiceResult)
    assert len(result.individual_values) == 0
    assert result.modifier == 5
    assert result.total == 5


def test_simulate_dice_roll_negative_modifier():
    """Test rolling with negative modifier."""
    roll = DiceRoll(num_dice=1, num_sides=20, modifier=-5)
    result = simulate_dice_roll(roll)

    assert isinstance(result, DiceResult)
    assert len(result.individual_values) == 1
    assert 1 <= result.individual_values[0] <= 20
    assert result.modifier == -5
    assert result.total == result.individual_values[0] - 5


@patch("random.randint")
def test_simulate_dice_roll_deterministic(mock_randint):
    """Test dice roll with mocked random values for deterministic testing."""
    # Set up mock to return specific values
    mock_randint.side_effect = [4, 6, 1]  # Will be used for 3d6

    roll = DiceRoll(num_dice=3, num_sides=6, modifier=2)
    result = simulate_dice_roll(roll)

    assert result.individual_values == [4, 6, 1]
    assert result.modifier == 2
    assert result.total == 13  # 4 + 6 + 1 + 2


def test_simulate_dice_roll_statistical():
    """Test that dice rolls follow expected statistical properties."""
    roll = DiceRoll(num_dice=1000, num_sides=6, modifier=0)
    result = simulate_dice_roll(roll)

    # Check that all values are within valid range
    assert all(1 <= value <= 6 for value in result.individual_values)

    # Check that we have a reasonable distribution of values
    value_counts = {}
    for value in result.individual_values:
        value_counts[value] = value_counts.get(value, 0) + 1

    # Each value should appear roughly 1/6 of the time (allowing for some variance)
    expected_count = 1000 / 6
    for count in value_counts.values():
        assert 0.8 * expected_count <= count <= 1.2 * expected_count


def test_simulate_dice_roll_edge_cases():
    """Test edge cases for dice rolling."""
    # Test with maximum possible values
    roll = DiceRoll(num_dice=100, num_sides=100, modifier=100)
    result = simulate_dice_roll(roll)
    assert len(result.individual_values) == 100
    assert all(1 <= value <= 100 for value in result.individual_values)
    assert result.modifier == 100

    # Test with minimum possible values
    roll = DiceRoll(num_dice=1, num_sides=1, modifier=0)
    result = simulate_dice_roll(roll)
    assert len(result.individual_values) == 1
    assert result.individual_values[0] == 1  # Only possible value for d1
    assert result.modifier == 0
    assert result.total == 1


# Tests for simulate_dice_statistics
NUM_SIMULATIONS = 10000  # Use a larger number for more stable statistical tests
TOLERANCE = 0.1  # Tolerance for comparing mean


def test_simulate_dice_statistics_basic():
    """Test statistics for a basic roll (2d6)."""
    roll = DiceRoll(num_dice=2, num_sides=6, modifier=0)
    stats = simulate_dice_statistics(roll, NUM_SIMULATIONS)

    assert isinstance(stats, DiceRollStats)
    assert stats.count == NUM_SIMULATIONS
    assert stats.minimum >= 2  # Theoretical min for 2d6 is 1+1=2
    assert stats.maximum <= 12  # Theoretical max for 2d6 is 6+6=12

    # Theoretical mean for 2d6 is 2 * (6+1)/2 = 7.0
    assert abs(stats.mean - 7.0) < TOLERANCE

    # Check bins structure and content
    assert isinstance(stats.bins, dict)
    assert sum(stats.bins.values()) == NUM_SIMULATIONS
    assert all(isinstance(k, int) for k in stats.bins.keys())
    assert all(isinstance(v, int) for v in stats.bins.values())
    assert all(2 <= total <= 12 for total in stats.bins.keys())


def test_simulate_dice_statistics_with_modifier():
    """Test statistics for a roll with a modifier (3d4+5)."""
    roll = DiceRoll(num_dice=3, num_sides=4, modifier=5)
    stats = simulate_dice_statistics(roll, NUM_SIMULATIONS)

    assert stats.count == NUM_SIMULATIONS
    # Theoretical min for 3d4+5 is 3*1+5 = 8
    # Theoretical max for 3d4+5 is 3*4+5 = 17
    assert stats.minimum >= 8
    assert stats.maximum <= 17

    # Theoretical mean for 3d4+5 is 3 * (4+1)/2 + 5 = 3 * 2.5 + 5 = 7.5 + 5 = 12.5
    assert abs(stats.mean - 12.5) < TOLERANCE
    assert sum(stats.bins.values()) == NUM_SIMULATIONS
    assert all(8 <= total <= 17 for total in stats.bins.keys())


def test_simulate_dice_statistics_one_simulation():
    """Test statistics with only one simulation."""
    roll = DiceRoll(num_dice=2, num_sides=8, modifier=-1)
    # Need to seed for reproducibility if we check exact values
    # For now, just check properties that hold true for 1 sim
    stats = simulate_dice_statistics(roll, 1)

    assert stats.count == 1
    # For 1 simulation, min, max, mean, median are the same single result
    single_result = list(stats.bins.keys())[0]  # Get the only key
    assert stats.minimum == single_result
    assert stats.maximum == single_result
    assert stats.mean == float(single_result)
    assert stats.median == float(single_result)
    assert stats.std_dev == 0.0  # Std dev is 0 for a single data point
    assert len(stats.bins) == 1
    assert stats.bins[single_result] == 1


def test_simulate_dice_statistics_deterministic():
    """Test statistics for a deterministic roll (5d1+10)."""
    roll = DiceRoll(num_dice=5, num_sides=1, modifier=10)
    stats = simulate_dice_statistics(roll, NUM_SIMULATIONS)

    expected_total = 5 * 1 + 10  # Always 15

    assert stats.count == NUM_SIMULATIONS
    assert stats.minimum == expected_total
    assert stats.maximum == expected_total
    assert stats.mean == expected_total
    assert stats.median == expected_total
    assert stats.std_dev == 0.0
    assert len(stats.bins) == 1
    assert stats.bins.get(expected_total) == NUM_SIMULATIONS


def test_simulate_dice_statistics_invalid_simulations():
    """Test that non-positive simulation counts raise ValueError."""
    roll = DiceRoll(num_dice=1, num_sides=6)

    with pytest.raises(ValueError, match="Number of simulations must be positive"):
        simulate_dice_statistics(roll, 0)

    with pytest.raises(ValueError, match="Number of simulations must be positive"):
        simulate_dice_statistics(roll, -100)
