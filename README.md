# 2D Spell Graph Simulation

A spatial physics simulation using graph topology for building a node-based spatial programming language for spells. This is a 2D prototype to explore behavior and physics before developing a 3D version.

## Overview

This simulation demonstrates a physics-based graph system where:
- **Nodes** have positions and accumulate instability from gravitational forces
- **Edges** connect nodes with paths that calculate tension based on bending angles
- Visual feedback through color coding shows force and tension states

## Features

### Nodes
- Position (x, y coordinates)
- Type system (currently: `basic`)
- Force and instability values calculated via gravity equation
- Color coding: Blue (stable) → Red (unstable)
- Black outline for visibility

### Edges
- SVG path format (D3-compatible)
- Tension calculation based on path bending angles
- Color coding: Green (low tension) → Yellow → Red (high tension)

### Physics
- Gravitational force between nodes: F = G / r²
- Nodes don't move but accumulate instability
- Real-time force calculations

## Project Structure

```
2d_spell_graph/
├── src/                      # Source code
│   ├── core/                 # Core graph components
│   │   ├── node.py          # Node class and NodeType enum
│   │   └── edge.py          # Edge class with path parsing
│   ├── physics/             # Physics calculations
│   │   └── forces.py        # Gravitational force calculations
│   └── simulation/          # Rendering and window management
│       └── window.py        # Main Arcade window
├── tests/                    # Test suite
│   └── test_simulation.py   # Component tests
├── configs/                  # Configuration files
│   └── default.json         # Default scene configuration
├── docs/                     # Documentation
├── main.py                   # Main entry point
├── run_simulation.sh         # Helper script to run simulation
├── run_tests.sh             # Helper script to run tests
└── requirements.txt         # Python dependencies
```

## Installation

```bash
pip install -r requirements.txt
```

## Running the Simulation

```bash
# Using the helper script
./run_simulation.sh

# Or directly with Python
PYTHONPATH=. python3 main.py
```

## Running Tests

```bash
# Using the helper script
./run_tests.sh

# Or directly with Python
PYTHONPATH=. python3 tests/test_simulation.py
```

## Configuration

The simulation loads from `configs/default.json`. Format:

```json
{
  "nodes": [
    {"x": 200, "y": 200, "type": "basic"}
  ],
  "edges": [
    {"path": "M 200,200 L 400,300"}
  ]
}
```

### Path Format
Uses SVG path syntax:
- `M x,y` - Move to position
- `L x,y` - Line to position

Example: `"M 100,100 L 200,200 L 300,150"` creates a bent line

## Module Organization

The codebase is organized into logical modules for easy extension:

- **`src/core/`** - Core graph components (nodes, edges)
  - Add new node types to `node.py`
  - Add new edge types or path commands to `edge.py`

- **`src/physics/`** - Physics calculations
  - Add new force types to `forces.py`
  - Create new physics modules as needed

- **`src/simulation/`** - Rendering and UI
  - Modify rendering in `window.py`
  - Add new visualization features

- **`configs/`** - Scene configurations
  - Create new JSON configs for different scenarios
  - Eventually: interactive editor will modify these

## Future Enhancements

- Interactive editor for creating/modifying graphs
- Additional node types with different behaviors
- More complex physics interactions (repulsion, springs, etc.)
- Edge effects based on tension
- Export/import system for spell graphs
- 3D version in a more efficient language

## Documentation

Additional documentation can be found in the `docs/` directory:
- [Magic System Architecture](docs/Magic-System-Architecture.md)
- [Simulation Terminology](docs/Simulation-Terminology.md)
