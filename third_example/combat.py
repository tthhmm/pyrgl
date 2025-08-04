"""Combat mechanics for the third example.

The goal of this module is to demonstrate a very small combat system.
Functions here operate on :class:`characters.Character` instances and
adjust their hit points based on the attacker's power.
"""
from __future__ import annotations

from .characters import Character


def attack(attacker: Character, defender: Character) -> int:
    """Apply damage from *attacker* to *defender* and return the damage dealt."""
    damage = attacker.power
    defender.take_damage(damage)
    return damage
