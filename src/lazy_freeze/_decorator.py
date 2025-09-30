import traceback
from collections.abc import Callable
from functools import wraps
from typing import Any, Literal, TypeVar, overload

__all__ = ["lazy_freeze"]

T = TypeVar("T")

# Core attribute mutation operations, always present via <object>
CORE_MUTATING_OPERATORS = {
    "__setattr__": lambda name, _: f"modify attribute '{name}' of",
    "__delattr__": lambda name: f"delete attribute '{name}' from",
}

# Optional mutating operations, modified only if exist
OPTIONAL_MUTATING_OPERATORS = {
    "__setitem__": lambda key, _: f"modify item '{key}' of",
    "__delitem__": lambda key: f"delete item '{key}' from",
    "__iadd__": lambda _: "modify with in-place addition",
    "__isub__": lambda _: "modify with in-place subtraction",
    "__imul__": lambda _: "modify with in-place multiplication",
    "__itruediv__": lambda _: "modify with in-place division",
    "__ifloordiv__": lambda _: "modify with in-place floor division",
    "__imod__": lambda _: "modify with in-place modulo",
    "__ipow__": lambda _: "modify with in-place power",
    "__ilshift__": lambda _: "modify with in-place left shift",
    "__irshift__": lambda _: "modify with in-place right shift",
    "__iand__": lambda _: "modify with in-place bitwise AND",
    "__ixor__": lambda _: "modify with in-place bitwise XOR",
    "__ior__": lambda _: "modify with in-place bitwise OR",
    # numpy-specific (operator '@'), but added for completeness
    "__imatmul__": lambda _: "modify with in-place matrix multiplication",
}


def get_error_message(self: Any, *, debug: bool, operation: str) -> str:
    if debug and hasattr(self, "__lazy_freeze_hash_stack_trace"):
        return (
            f"Cannot {operation} {self.__class__.__name__} after its hash has been taken.\n"
            f"Hash was calculated at:\n{self.__lazy_freeze_hash_stack_trace}"
        )
    return f"Cannot {operation} {self.__class__.__name__} after its hash has been taken"


# Create a wrapped method that checks hash_taken
def make_protected_method(
    *,
    method_name: str,
    original_method: Callable,
    error_formatter: Callable,
    debug: bool,
) -> Callable:
    def protected_method(self: Any, *args: Any, **kwargs: Any) -> Any:
        if not getattr(self, "__lazy_freeze_hash_taken", False):
            return original_method(self, *args, **kwargs)

        # For __setattr__ and __delattr__, check if the attribute is protected, the first argument is the attribute name
        if (
            method_name in CORE_MUTATING_OPERATORS
            and (frozen_attrs := self.__lazy_freeze_frozen_attrs) != "all"
            and args[0] not in frozen_attrs
        ):
            return original_method(self, *args, **kwargs)

        # Generate the appropriate error message
        op_msg = error_formatter(*args)
        raise RuntimeError(get_error_message(self, debug=debug, operation=op_msg))

    return protected_method


def ensure_freezable(cls: type[T]) -> None:
    if not isinstance(cls, type):
        msg = f"@lazy_freeze can only be applied to classes. Got {cls} which is of type '{type(cls).__name__}'."
        raise TypeError(msg)

    has_custom_hash = hasattr(cls, "__hash__") and cls.__hash__ is not object.__hash__
    if not has_custom_hash:
        msg = (
            f"Class '{cls.__name__}' must implement __hash__ to use the @lazy_freeze decorator. "
            "Implement __hash__ to define the object's hash value, which should be consistent with equality "
            "(__eq__)."
        )
        raise TypeError(msg)


def create_methods_override(cls: type[T]) -> dict[str, tuple[Callable, Callable]]:
    methods_override = {}

    # Update core methods if the class has its own implementations
    for op_name, error_formatter in CORE_MUTATING_OPERATORS.items():
        methods_override[op_name] = (getattr(cls, op_name, getattr(object, op_name)), error_formatter)

    # Only add optional operations that exist in the class
    for op_name, error_formatter in OPTIONAL_MUTATING_OPERATORS.items():
        if hasattr(cls, op_name):
            methods_override[op_name] = (getattr(cls, op_name), error_formatter)

    return methods_override


def wrap_hash(
    *,
    debug: bool,
    freeze_attrs: Literal["all", "dynamic"] | frozenset[str] | None,
    cache_hash: bool,
    original_hash: Callable[[T], int],
) -> Callable[[T], int]:
    @wraps(original_hash)
    def patched_hash(self: T) -> int:
        """Calculate hash and mark the object as hash-taken. In debug mode, capture stack trace."""
        if cache_hash:
            try:
                if object.__getattribute__(self, "__lazy_freeze_hash_taken"):
                    return object.__getattribute__(self, "__lazy_freeze_cached_hash")
            except AttributeError:
                pass

        if freeze_attrs == "dynamic":
            object.__setattr__(self, "__lazy_freeze_used_attributes", set())
            object.__setattr__(self, "__lazy_freeze_taking_hash", True)

        hash_value = original_hash(self)

        if cache_hash:
            object.__setattr__(self, "__lazy_freeze_cached_hash", hash_value)

        if freeze_attrs == "dynamic":
            object.__delattr__(self, "__lazy_freeze_taking_hash")
            object.__setattr__(
                self,
                "__lazy_freeze_frozen_attrs",
                frozenset(object.__getattribute__(self, "__lazy_freeze_used_attributes")),
            )
            object.__delattr__(self, "__lazy_freeze_used_attributes")
        else:
            object.__setattr__(self, "__lazy_freeze_frozen_attrs", freeze_attrs)

        # Use direct attribute setting to avoid recursion with cls.__setattr__
        object.__setattr__(self, "__lazy_freeze_hash_taken", True)

        if debug:
            stack_trace = "".join(traceback.format_stack()[:-1])  # Exclude current frame
            object.__setattr__(self, "__lazy_freeze_hash_stack_trace", stack_trace)

        return hash_value

    return patched_hash


def wrap_getattribute(*, original_getattribute: Callable[[T, str], Any]) -> Callable[[T, str], Any]:
    @wraps(original_getattribute)
    def patched_getattribute(self: T, name: str) -> Any:
        """Get attribute and record the retrieved attributes used for calculating hash."""
        try:
            taking_hash = object.__getattribute__(self, "__lazy_freeze_taking_hash")
        except AttributeError:
            taking_hash = False

        if not taking_hash:
            return original_getattribute(self, name)

        object.__getattribute__(self, "__lazy_freeze_used_attributes").add(name)

        return original_getattribute(self, name)

    return patched_getattribute


@overload
def lazy_freeze(
    cls_external: None = None,
    /,
    *,
    debug: bool = False,
    freeze_attrs: Literal["all", "dynamic"] | frozenset[str] | None = "all",
    cache_hash: bool = False,
) -> Callable[[type[T]], type[T]]: ...


@overload
def lazy_freeze(
    cls_external: type[T],
    /,
    *,
    debug: bool = False,
    freeze_attrs: Literal["all", "dynamic"] | frozenset[str] | None = "all",
    cache_hash: bool = False,
) -> type[T]: ...


def lazy_freeze(
    cls_external: type[T] | None = None,
    /,
    *,
    debug: bool = False,
    freeze_attrs: Literal["all", "dynamic"] | frozenset[str] | None = "all",
    cache_hash: bool = False,
) -> type[T] | Callable[[type[T]], type[T]]:
    """Class decorator that makes an object immutable after its hash is calculated.

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
        ensure_freezable(cls)

        cls.__hash__ = wrap_hash(
            debug=debug,
            freeze_attrs=freeze_attrs,
            cache_hash=cache_hash,
            original_hash=cls.__hash__,
        )

        if freeze_attrs == "dynamic":
            cls.__getattribute__ = wrap_getattribute(original_getattribute=cls.__getattribute__)

        # Create new methods for each mutating operation
        methods_override = create_methods_override(cls)
        for method_name, (original_method, error_formatter) in methods_override.items():
            # Set the method on the class
            setattr(
                cls,
                method_name,
                make_protected_method(
                    method_name=method_name,
                    original_method=original_method,
                    error_formatter=error_formatter,
                    debug=debug,
                ),
            )

        return cls

    if cls_external is not None:
        # @lazy_freeze used without parameters, return the class directly
        return decorator(cls_external)

    return decorator
