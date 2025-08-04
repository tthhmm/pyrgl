"""Tests for :mod:`third_example.map`.

The tests modify :data:`sys.path` so that the project root is available
on the import path when tests are executed from within the ``tests``
directory.
"""
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from third_example import map as map_module


def test_create_map_dimensions():
    game_map = map_module.create_map(5, 3)
    assert len(game_map) == 3
    assert all(len(row) == 5 for row in game_map)


def test_is_blocked_detects_walls():
    game_map = map_module.create_map(2, 2)
    game_map[0][0] = "#"
    assert map_module.is_blocked(0, 0, game_map)
    assert not map_module.is_blocked(1, 1, game_map)
