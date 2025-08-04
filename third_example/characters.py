"""Character definitions for the third example.

The :class:`Character` class is intentionally lightweight and holds only
attributes required for the accompanying unit tests.  Real games would
include many more features such as inventory management and AI.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Character:
    """Basic game character.

    Parameters
    ----------
    name:
        Human readable identifier of the character.
    hp:
        Hit points representing the amount of damage the character can
        withstand.
    power:
        Attack strength used in combat calculations.
    """

    name: str
    hp: int
    power: int

    def take_damage(self, amount: int) -> None:
        """Reduce :attr:`hp` by ``amount`` down to a minimum of zero."""
        self.hp = max(0, self.hp - amount)


class Player(Character):
    """Player controlled character."""


class Monster(Character):
    """Non-player character used for combat demonstrations."""
