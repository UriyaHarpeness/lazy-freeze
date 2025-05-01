"""
lazy_freeze - A decorator that makes objects immutable after their hash is calculated.

This module provides a class decorator that adds or overrides the __hash__, __setattr__,
and __setitem__ methods of a class to prevent modifications after the object's hash
has been calculated.
"""

import traceback
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union, cast, overload

# Type variable for the class being decorated
T = TypeVar('T', bound=Type[object])


@overload
def lazy_freeze(cls: T) -> T:
    ...


@overload
def lazy_freeze(cls: None = None, *, debug: bool = False) -> Callable[[T], T]:
    ...


def lazy_freeze(cls: Optional[T] = None, *, debug: bool = False) -> Union[T, Callable[[T], T]]:
    """
    Class decorator that makes an object immutable after its hash is calculated.

    The decorator adds or overrides:
    - __hash__: to set hash_taken=True when called
    - __setattr__, __delattr__: to prevent attribute modification if hash_taken is True
    - __setitem__, __delitem__: to prevent item modification if hash_taken is True
    - In-place operations (__iadd__, __isub__, etc.): to prevent in-place modifications

    Args:
        cls: The class to be decorated
        debug: If True, captures stack trace at hash time and includes it in error messages

    Returns:
        The decorated class

    Raises:
        AssertionError: If the class does not have a custom __hash__ method

    Example:
        @lazy_freeze
        class Person:
            def __init__(self, name, age):
                self.name = name
                self.age = age

            def __hash__(self):
                return hash((self.name, self.age))

        # With debug enabled
        @lazy_freeze(debug=True)
        class DebugPerson:
            def __init__(self, name, age):
                self.name = name
                self.age = age

            def __hash__(self):
                return hash((self.name, self.age))
    """
    def decorator(cls: T) -> T:
        # Check if class has a custom __hash__ method (not the one from object)
        has_custom_hash = hasattr(
            cls, '__hash__') and cls.__hash__ is not object.__hash__

        # Assert that the class has a custom hash implementation
        assert has_custom_hash, (
            f"Class '{cls.__name__}' must implement a custom __hash__ method to use the @lazy_freeze decorator. "
            f"Implement __hash__ to define the object's hash value, which should be consistent with equality (__eq__)."
        )

        # Store original methods
        original_hash = cls.__hash__
        original_setattr = cast(Callable[[Any, str, Any], None],
                                cls.__setattr__ if hasattr(cls, '__setattr__') else object.__setattr__)
        original_delattr = cast(Callable[[Any, str], None],
                                cls.__delattr__ if hasattr(cls, '__delattr__') else object.__delattr__)
        original_setitem = cast(Optional[Callable[[Any, Any, Any], None]],
                                cls.__setitem__ if hasattr(cls, '__setitem__') else None)
        original_delitem = cast(Optional[Callable[[Any, Any], None]],
                                cls.__delitem__ if hasattr(cls, '__delitem__') else None)

        # In-place operation methods to protect
        inplace_operations: List[str] = [
            '__iadd__', '__isub__', '__imul__', '__itruediv__', '__ifloordiv__',
            '__imod__', '__ipow__', '__ilshift__', '__irshift__', '__iand__',
            '__ixor__', '__ior__'
        ]

        # Store original in-place operations
        original_inplace: Dict[str, Callable[[Any, Any], Any]] = {}
        for op in inplace_operations:
            if hasattr(cls, op):
                original_inplace[op] = getattr(cls, op)

        def __hash__(self: Any) -> int:
            """Calculate hash and mark the object as hash-taken. In debug mode, capture stack trace."""
            hash_value = original_hash(self)

            # In debug mode, capture stack trace
            if debug:
                stack_trace = ''.join(traceback.format_stack()[
                                      :-1])  # Exclude current frame
                original_setattr(self, 'hash_taken', True)
                original_setattr(self, '_hash_stack_trace', stack_trace)
            else:
                original_setattr(self, 'hash_taken', True)

            return hash_value

        def get_error_message(self: Any, operation: str) -> str:
            """Generate an appropriate error message based on debug mode."""
            if debug and hasattr(self, '_hash_stack_trace'):
                return (
                    f"Cannot {operation} {cls.__name__} after its hash has been taken.\n"
                    f"Hash was calculated at:\n{self._hash_stack_trace}"
                )
            else:
                return f"Cannot {operation} {cls.__name__} after its hash has been taken"

        def __setattr__(self: Any, name: str, value: Any) -> None:
            """Prevent attribute modification if hash has been taken."""
            if hasattr(self, 'hash_taken') and self.hash_taken:
                raise TypeError(get_error_message(
                    self, f"modify attribute '{name}' of"))
            original_setattr(self, name, value)

        def __delattr__(self: Any, name: str) -> None:
            """Prevent attribute deletion if hash has been taken."""
            if hasattr(self, 'hash_taken') and self.hash_taken:
                raise TypeError(get_error_message(
                    self, f"delete attribute '{name}' from"))
            original_delattr(self, name)

        def __setitem__(self: Any, key: Any, value: Any) -> None:
            """Prevent item modification if hash has been taken."""
            if hasattr(self, 'hash_taken') and self.hash_taken:
                raise TypeError(get_error_message(
                    self, f"modify item '{key}' of"))
            if original_setitem is not None:
                original_setitem(self, key, value)
            else:
                raise TypeError(
                    f"{cls.__name__} does not support item assignment")

        def __delitem__(self: Any, key: Any) -> None:
            """Prevent item deletion if hash has been taken."""
            if hasattr(self, 'hash_taken') and self.hash_taken:
                raise TypeError(get_error_message(
                    self, f"delete item '{key}' from"))
            if original_delitem is not None:
                original_delitem(self, key)
            else:
                raise TypeError(
                    f"{cls.__name__} does not support item deletion")

        # Replace methods
        cls.__hash__ = __hash__
        cls.__setattr__ = __setattr__
        cls.__delattr__ = __delattr__

        # Only add item methods if the class supports them
        if hasattr(cls, '__setitem__') or original_setitem is not None:
            cls.__setitem__ = __setitem__

        if hasattr(cls, '__delitem__') or original_delitem is not None:
            cls.__delitem__ = __delitem__

        # Create and add in-place operation methods
        for op in inplace_operations:
            if op in original_inplace:
                # Create a function that checks hash_taken before calling the original
                def make_inplace_method(op_name: str, original_method: Callable[[Any, Any], Any]) \
                        -> Callable[[Any, Any], Any]:
                    def inplace_method(self: Any, other: Any) -> Any:
                        if hasattr(self, 'hash_taken') and self.hash_taken:
                            raise TypeError(get_error_message(
                                self, f"modify with {op_name}"))
                        return original_method(self, other)
                    return inplace_method

                # Set the method on the class
                setattr(cls, op, make_inplace_method(op, original_inplace[op]))

        return cls

    # Handle both @lazy_freeze and @lazy_freeze(debug=True) syntax
    if cls is None:
        return decorator
    return decorator(cls)
