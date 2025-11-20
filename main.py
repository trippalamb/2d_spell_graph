#!/usr/bin/env python3
"""Main entry point for the spell graph simulation."""
import arcade
from src.simulation import GraphSimulation


def main():
    """Run the spell graph simulation."""
    window = GraphSimulation()
    window.setup()
    arcade.run()


if __name__ == "__main__":
    main()
