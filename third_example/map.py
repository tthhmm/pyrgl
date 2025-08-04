"""Map creation and utilities.

This module provides functions for creating a game map represented as
simple two dimensional lists.  It intentionally keeps the feature set
minimal so that it can be used as a teaching example for how to
structure larger projects.
"""
from __future__ import annotations

from typing import List

Tile = str
MapGrid = List[List[Tile]]


def create_map(width: int, height: int, fill: Tile = ".") -> MapGrid:
    """Return a new map filled with *fill* tiles.

    Parameters
    ----------
    width, height:
        Dimensions of the map to create.
    fill:
        Character used for all tiles.  The default is ``"."`` which
        represents a walkable floor.
    """
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive")
    return [[fill for _ in range(width)] for _ in range(height)]


def is_blocked(x: int, y: int, game_map: MapGrid) -> bool:
    """Return ``True`` if the tile at *x*, *y* is not walkable.

    For this educational example every tile except ``'#'`` is walkable.
    """
    try:
        return game_map[y][x] == "#"
    except IndexError:
        raise IndexError("coordinates out of bounds")
