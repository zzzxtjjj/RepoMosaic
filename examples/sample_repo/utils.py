"""Utility functions used by the sample repository."""


def calculate_distance(start: float, end: float) -> float:
    """Calculate the absolute distance between two positions."""
    return abs(end - start)


def load_config() -> dict[str, str]:
    """Return a small in-memory sample configuration."""
    return {"name": "Atlas"}
