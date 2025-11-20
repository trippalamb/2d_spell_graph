# 2D Spell Graph Simulation

A spatial physics simulation using graph topology for node-based spatial programming language prototype.

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

## Installation

```bash
pip install -r requirements.txt
```

## Running the Simulation

```bash
python3 simulation.py
```

## Configuration

The simulation loads from `config.json`. Format:

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

## Project Structure

- `node.py` - Node class and node type enum
- `edge.py` - Edge class with path parsing and tension calculations
- `physics.py` - Gravity-based force calculations
- `simulation.py` - Main Arcade window and rendering
- `config.json` - Scene configuration

## Future Enhancements

- Interactive editor for creating/modifying graphs
- Additional node types
- More complex physics interactions
- 3D version in efficient language
