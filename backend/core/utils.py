"""Shared utility functions used across Django apps."""


def safe_int(value: str | None, default: int, min_val: int = 1, max_val: int = 1000) -> int:
    """Safely convert a query parameter to int with bounds."""
    if value is None:
        return default
    try:
        return max(min_val, min(int(value), max_val))
    except (ValueError, TypeError):
        return default
