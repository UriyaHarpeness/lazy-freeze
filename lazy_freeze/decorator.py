import traceback
from typing import Any, TypeVar, overload
from collections.abc import Callable


T = TypeVar('T')


@overload
def lazy_freeze(
    cls_external: None = None,
    debug: bool = False,
    freeze_attrs: list[str] | None = None,
) -> Callable[[type[T]], type[T]]: ...


@overload
def lazy_freeze(
    cls_external: type[T],
    debug: bool = False,
    freeze_attrs: list[str] | None = None,
) -> type[T]: ...


def lazy_freeze(
    cls_external: type[T] | None = None,
    debug: bool = False,
    freeze_attrs: list[str] | None = None,
) -> type[T] | Callable[[type[T]], type[T]]:
    """
    Class decorator that makes an object immutable after its hash is calculated.
    Works only on classes, and furthermore: classes that implement or inherit __hash__.

    The decorator overrides:
    - __hash__: to set hash_taken=True when called
    - __setattr__, __delattr__: to prevent attribute modification if hash_taken is True
    And if existing, also overrides:
    - __setitem__, __delitem__: to prevent item modification if hash_taken is True
    - In-place operations (__iadd__, __isub__, etc.): to prevent in-place modifications

    Optional decorator parameters:
        debug: capture stack-trace at point of hash and report it when code tries to modify the object
        freeze_attrs: List of attribute names to freeze after hash is taken.
                         If None or empty, all attributes will be frozen.
    """
    def decorator(cls: type[T]) -> type[T]:
        if not isinstance(cls, type):
            raise TypeError(f"@lazy_freeze can only be applied to classes. "
                            f"Got {cls} which is of type '{type(cls).__name__}'.")

        has_custom_hash = hasattr(cls, '__hash__') and cls.__hash__ is not object.__hash__
        assert has_custom_hash, (
            f"Class '{cls.__name__}' must implement __hash__ to use the @lazy_freeze decorator. "
            f"Implement __hash__ to define the object's hash value, which should be consistent with equality (__eq__)."
        )

        original_hash = cls.__hash__

        # Core attribute mutation operations, always present via <object>
        overridden_methods = {
            '__setattr__': (object.__setattr__,
                            lambda name, value: f"modify attribute '{name}' of"),
            '__delattr__': (object.__delattr__,
                            lambda name: f"delete attribute '{name}' from"),
        }

        # Optional mutating operations, modified only if exist
        optional_ops = {
            '__setitem__': lambda key, value: f"modify item '{key}' of",
            '__delitem__': lambda key: f"delete item '{key}' from",
            '__iadd__': lambda other: "modify with in-place addition",
            '__isub__': lambda other: "modify with in-place subtraction",
            '__imul__': lambda other: "modify with in-place multiplication",
            '__itruediv__': lambda other: "modify with in-place division",
            '__ifloordiv__': lambda other: "modify with in-place floor division",
            '__imod__': lambda other: "modify with in-place modulo",
            '__ipow__': lambda other: "modify with in-place power",
            '__ilshift__': lambda other: "modify with in-place left shift",
            '__irshift__': lambda other: "modify with in-place right shift",
            '__iand__': lambda other: "modify with in-place bitwise AND",
            '__ixor__': lambda other: "modify with in-place bitwise XOR",
            '__ior__': lambda other: "modify with in-place bitwise OR",

            # numpy-specific (operator '@'), but added for completeness
            '__imatmul__': lambda other: "modify with in-place matrix multiplication",
        }

        # Only add optional operations that exist in the class
        for op_name, error_formatter in optional_ops.items():
            if hasattr(cls, op_name):
                original_method = getattr(cls, op_name)
                overridden_methods[op_name] = (original_method, error_formatter)

        # Update core methods if the class has its own implementations
        for method_name in list(overridden_methods.keys()):
            if method_name in ('__setattr__', '__delattr__') and hasattr(cls, method_name):
                overridden_methods[method_name] = (getattr(cls, method_name),
                                                   overridden_methods[method_name][1])

        def new_hash(self: T) -> int:
            """Calculate hash and mark the object as hash-taken. In debug mode, capture stack trace."""
            hash_value = original_hash(self)

            # Use direct attribute setting to avoid recursion with cls.__setattr__
            object.__setattr__(self, 'hash_taken', True)

            if debug:
                stack_trace = ''.join(traceback.format_stack()[:-1])  # Exclude current frame
                object.__setattr__(self, '_hash_stack_trace', stack_trace)

            return hash_value

        def get_error_message(self: Any, operation: str) -> str:
            if debug and hasattr(self, '_hash_stack_trace'):
                return (
                    f"Cannot {operation} {cls.__name__} after its hash has been taken.\n"
                    f"Hash was calculated at:\n{self._hash_stack_trace}"
                )
            else:
                return f"Cannot {operation} {cls.__name__} after its hash has been taken"

        cls.__hash__ = new_hash

        # Create new methods for each mutating operation
        for method_name, (original_method, error_formatter) in overridden_methods.items():
            # Skip if the original method doesn't exist and it's not a core attribute method
            if original_method is None and method_name not in ('__setattr__', '__delattr__'):
                continue

            # Create a wrapped method that checks hash_taken
            def make_protected_method(method_name=method_name,
                                      original=original_method,
                                      format_error=error_formatter):
                def protected_method(self: Any, *args: Any, **kwargs: Any) -> Any:
                    if hasattr(self, 'hash_taken') and self.hash_taken:
                        # Check if we're only protecting specific attributes
                        if freeze_attrs:
                            # For __setattr__ and __delattr__, check if the attribute is protected
                            if method_name == '__setattr__' or method_name == '__delattr__':
                                attr_name = args[0] if args else None
                                if attr_name not in freeze_attrs:
                                    return original(self, *args, **kwargs)

                        # Generate the appropriate error message
                        op_msg = format_error(*args)
                        raise TypeError(get_error_message(self, op_msg))

                    return original(self, *args, **kwargs)

                return protected_method

            # Set the method on the class
            setattr(cls, method_name, make_protected_method())

        return cls

    if cls_external is not None:
        # @lazy_freeze used without parameters, return the class directly
        return decorator(cls_external)
    else:
        return decorator
