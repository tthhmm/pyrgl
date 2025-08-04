"""Item definitions used by the third example.

Items are intentionally small and contain only the data needed for unit
Tests.  They can be extended with additional behaviour such as being
usable or equippable.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Item:
    """Simple item with a name and an optional power bonus."""

    name: str
    power_bonus: int = 0
