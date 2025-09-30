"""lazy_freeze - A decorator that makes objects immutable after their hash is calculated.

This module provides a class decorator that adds or overrides the __hash__, __setattr__,
and other special methods of a class to prevent modifications after the object's hash
has been calculated.
"""

from src.lazy_freeze._decorator import lazy_freeze

__version__ = "0.2.0"
__all__ = ["lazy_freeze"]
