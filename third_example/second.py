"""Entry point combining all modules of the third example.

Running this module as a script will create a small map, instantiate a
player and a monster and perform one attack so developers can see the
modules interact.
"""
from __future__ import annotations

from . import characters, combat, map as map_module


def setup_demo():
    """Create a demo map and two characters."""
    game_map = map_module.create_map(10, 10)
    player = characters.Player(name="Hero", hp=30, power=5)
    monster = characters.Monster(name="Orc", hp=10, power=3)
    return game_map, player, monster


def main() -> None:
    """Run a very small combat demonstration."""
    _, player, monster = setup_demo()
    damage = combat.attack(player, monster)
    print(f"{player.name} attacks {monster.name} for {damage} hit points!")
    print(f"{monster.name} has {monster.hp} HP left.")


if __name__ == "__main__":  # pragma: no cover - manual demonstration
    main()
