import random
import re
from collections import Counter
from dataclasses import dataclass
from statistics import mean, median, stdev


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


@dataclass
class DiceRollStats:
    """Statistics from multiple dice roll simulations."""

    count: int
    minimum: int
    maximum: int
    mean: float
    median: float
    std_dev: float
    bins: dict[int, int]  # Maps total value to frequency


class DiceParsingError(Exception):
    """Raised when the dice roll notation cannot be parsed correctly."""

    ...


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


def simulate_dice_statistics(roll: DiceRoll, num_simulations: int) -> DiceRollStats:
    """
    Run multiple dice roll simulations and collect statistics.

    Args:
        roll: A DiceRoll object specifying the dice configuration
        num_simulations: Number of simulations to run

    Returns:
        DiceRollStats: Statistics collected from the simulations
    """
    if num_simulations <= 0:
        raise ValueError("Number of simulations must be positive")

    # Run all simulations and collect total values
    all_results = []
    for _ in range(num_simulations):
        result = simulate_dice_roll(roll)
        all_results.append(result.total)

    # Calculate frequency distribution
    bins = dict(Counter(all_results))

    # Calculate statistics
    stats = DiceRollStats(
        count=num_simulations,
        minimum=min(all_results),
        maximum=max(all_results),
        mean=mean(all_results),
        median=median(all_results),
        std_dev=stdev(all_results) if num_simulations > 1 else 0,
        bins=bins,
    )

    return stats


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


def parse_and_execute_command(command_string: str):
    """
    Parse and execute a dice roll command.

    Commands:
    - r/roll <dice_string>: Roll dice once
    - s/stats/statistics N <dice_string>: Run N simulations and show statistics

    Args:
        command_string: The command to execute

    Returns:
        DiceResult or DiceRollStats depending on the command

    Raises:
        ValueError: If the command format is invalid
    """
    command_string = command_string.strip()
    parts = command_string.split(maxsplit=2)  # Split potentially up to 3 parts
    command = parts[0].lower() if parts else ""

    # Handle roll command
    if command in ("r", "roll"):
        if len(parts) < 2:
            raise ValueError("Missing dice specification")

        # Join parts after the command to get the full dice string
        dice_string = " ".join(parts[1:]).strip()
        try:
            roll = parse_dice_roll(dice_string)
            return simulate_dice_roll(roll)
        except DiceParsingError as e:
            raise ValueError(f"Invalid dice format: {e}")

    # Handle stats command
    elif command in ("s", "stats", "statistics"):
        if len(parts) < 3:
            raise ValueError("Missing number of simulations or dice specification")

        try:
            num_simulations = int(parts[1])
        except ValueError:
            raise ValueError("Number of simulations must be an integer")

        if num_simulations <= 0:
            raise ValueError("Number of simulations must be positive")

        dice_string = parts[2].strip()
        try:
            roll = parse_dice_roll(dice_string)
            return simulate_dice_statistics(roll, num_simulations)
        except DiceParsingError as e:
            raise ValueError(f"Invalid dice format: {e}")

    # Handle unknown or empty command
    else:
        if not command:  # Handle empty or whitespace-only input
            raise ValueError(
                "Unknown command. Use 'roll <dice>' or 'stats <num> <dice>'"
            )  # Or a different message?
        # Treat any other non-empty input as an unknown command
        raise ValueError(
            f"Unknown command: '{command}'. Use 'roll <dice>' or 'stats <num> <dice>'"
        )
