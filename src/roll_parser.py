import random
import re
from dataclasses import dataclass


@dataclass
class DiceRoll:
    num_dice: int
    num_sides: int
    modifier: int = 0


@dataclass
class DiceResult:
    """Result of a dice roll, including individual values and total."""

    individual_values: list[int]
    modifier: int = 0

    @property
    def total(self) -> int:
        """Calculate the total value of the roll including modifier."""
        return sum(self.individual_values) + self.modifier


class DiceParsingError(Exception):
    """Raised when the dice roll notation cannot be parsed correctly."""

    ...


def parse_dice_roll(dice_string: str) -> DiceRoll:
    """
    Parse a dice roll string in the format xdy, xdy+z, or xdy-z.

    Args:
        dice_string: A string representing a dice roll.

    Returns:
        DiceRoll: A dataclass containing the parsed components.

    Raises:
        DiceParsingError: If the string cannot be parsed correctly.
    """
    # Remove all whitespace and convert to lowercase
    dice_string = dice_string.replace(" ", "").lower()

    # Regular expression to match valid dice roll formats
    pattern = r"^(\d+)d(\d+)([+-]\d+)?$"

    match = re.match(pattern, dice_string)

    if not match:
        raise DiceParsingError(f"Invalid dice roll format: {dice_string}")

    num_dice = int(match.group(1))
    num_sides = int(match.group(2))

    # Handle the modifier if present
    modifier = 0
    if match.group(3):
        modifier = int(match.group(3))

    return DiceRoll(num_dice=num_dice, num_sides=num_sides, modifier=modifier)


def simulate_dice_roll(roll: DiceRoll) -> DiceResult:
    """
    Simulate rolling dice based on the provided DiceRoll specification.

    Args:
        roll: A DiceRoll object specifying the number of dice, sides, and modifier.

    Returns:
        DiceResult: The result of the dice roll, including individual values and total.
    """
    # Generate random values for each die
    values = [random.randint(1, roll.num_sides) for _ in range(roll.num_dice)]

    # Return the DiceResult with individual values and modifier
    return DiceResult(individual_values=values, modifier=roll.modifier)
