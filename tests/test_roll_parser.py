from unittest.mock import patch

import pytest

from roll_parser import (
    DiceParsingError,
    DiceResult,
    DiceRoll,
    parse_dice_roll,
    simulate_dice_roll,
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
