# pyrgl
Just try to learn to write one rogue like game via python

## third_example package

The `third_example` package demonstrates how the project is structured across several small modules:

- `map.py` – functions for creating and querying a simple two-dimensional map grid.
- `characters.py` – lightweight `Player` and `Monster` classes.
- `combat.py` – a minimal combat system that applies damage based on power.
- `items.py` – basic item definitions that can grant power bonuses.
- `second.py` – entry point that wires everything together for a short demonstration.

### Running the demo

Execute the demo from the repository root:

```
python -m third_example.second
```

This will build a map, spawn a hero and a monster, and print the results of a single attack.

### Running tests

The test suite uses `pytest` and can be run with:

```
pytest
```

All tests should pass, producing output similar to:

```
3 passed in 0.02s
```
