"""Tests for :mod:`third_example.combat`.

The tests modify :data:`sys.path` so that the project root is available
on the import path when tests are executed from within the ``tests``
directory.
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from third_example.characters import Player, Monster
from third_example import combat


def test_attack_reduces_hp():
    attacker = Player(name="Hero", hp=30, power=4)
    defender = Monster(name="Orc", hp=10, power=3)
    damage = combat.attack(attacker, defender)
    assert damage == 4
    assert defender.hp == 6
