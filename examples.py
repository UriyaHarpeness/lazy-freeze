#!/usr/bin/env python3
"""
Examples demonstrating the usage of the lazy_freeze decorator.
"""

from lazy_freeze import lazy_freeze


# Example 1: Regular class with attributes
@lazy_freeze
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def __hash__(self):
        return hash((self.name, self.age))

    def __eq__(self, other):
        if not isinstance(other, Person):
            return False
        return self.name == other.name and self.age == other.age

    def __repr__(self):
        return f"Person(name='{self.name}', age={self.age})"


# Example 2: Dictionary-like class
@lazy_freeze
class CustomDict(dict):
    """A dictionary that becomes immutable after its hash is taken."""

    def __hash__(self):
        # Custom hash for dictionary
        return hash(tuple(sorted(self.items())))


# Example of class that inherits a custom hash method
class ParentWithHash:
    def __hash__(self):
        return hash(id(self))  # Simple hash but not object.__hash__


@lazy_freeze
class ChildWithInheritedHash(ParentWithHash):
    """Class that inherits a hash method from its parent."""

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"ChildWithInheritedHash(value={self.value})"


# Example of class with in-place operations
@lazy_freeze
class Counter:
    """Demonstrates protection of in-place operations."""

    def __init__(self, value=0):
        self.value = value

    def __hash__(self):
        return hash(self.value)

    def __eq__(self, other):
        if not isinstance(other, Counter):
            return False
        return self.value == other.value

    def __iadd__(self, other):
        if isinstance(other, Counter):
            self.value += other.value
        else:
            self.value += other
        return self

    def __isub__(self, other):
        if isinstance(other, Counter):
            self.value -= other.value
        else:
            self.value -= other
        return self

    def __repr__(self):
        return f"Counter(value={self.value})"


# Example of class with __delitem__ and __delattr__
@lazy_freeze
class AttributeContainer:
    """Demonstrates protection of attribute and item deletion."""

    def __init__(self, **kwargs):
        self.items = {}
        for key, value in kwargs.items():
            setattr(self, key, value)
            self.items[key] = value

    def __hash__(self):
        # Hash based on sorted items
        attr_items = tuple(sorted((k, v)
                           for k, v in self.__dict__.items() if k != 'items'))
        return hash(attr_items)

    def __delattr__(self, name):
        if name in self.__dict__:
            super().__delattr__(name)

    def __delitem__(self, key):
        if key in self.items:
            del self.items[key]

    def __repr__(self):
        attrs = ', '.join(f"{k}={v!r}" for k, v in self.__dict__.items()
                          if k != 'items' and not k.startswith('_'))
        return f"AttributeContainer({attrs})"


# New example with debug=True parameter
@lazy_freeze(debug=True)
class DebugPerson:
    """Class that demonstrates debug mode with stack traces."""

    def __init__(self, name, age):
        self.name = name
        self.age = age

    def __hash__(self):
        return hash((self.name, self.age))

    def __eq__(self, other):
        if not isinstance(other, DebugPerson):
            return False
        return self.name == other.name and self.age == other.age

    def __repr__(self):
        return f"DebugPerson(name='{self.name}', age={self.age})"


# Helpers for the demo

def hash_object(obj):
    """Hash an object and return the hash."""
    return hash(obj)


def modify_object(obj):
    """Try to modify an object."""
    obj.age = 999


# Regular demos

def demonstrate_person():
    """Demonstrate lazy freezing on a Person instance."""
    print("\n=== Person Example ===")

    # Create a person
    p = Person("Alice", 30)
    print(f"Created: {p}")

    # Modify before hash
    p.age = 31
    print(f"Modified before hash: {p}")

    # Take the hash (this will set hash_taken=True)
    h = hash(p)
    print(f"Hash value: {h}")
    print(f"hash_taken attribute: {getattr(p, 'hash_taken', False)}")

    # Try to modify after hash
    try:
        p.age = 32
        print(f"Modified after hash: {p}")  # This should not execute
    except TypeError as e:
        print(f"Exception when modifying after hash: {e}")


def demonstrate_dict():
    """Demonstrate lazy freezing on a dictionary-like object."""
    print("\n=== Dictionary Example ===")

    # Create a dictionary
    d = CustomDict(a=1, b=2)
    print(f"Created: {d}")

    # Modify before hash
    d["c"] = 3
    print(f"Modified before hash: {d}")

    # Take the hash (this will set hash_taken=True)
    h = hash(d)
    print(f"Hash value: {h}")
    print(f"hash_taken attribute: {getattr(d, 'hash_taken', False)}")

    # Try to modify after hash
    try:
        d["d"] = 4
        print(f"Modified after hash: {d}")  # This should not execute
    except TypeError as e:
        print(f"Exception when modifying after hash: {e}")


def demonstrate_dict_usage():
    """Demonstrate how lazy_freeze prevents issues with dictionaries."""
    print("\n=== Using in Dictionary ===")

    # Create original people
    p1 = Person("Bob", 25)
    p2 = Person("Carol", 35)

    # Use as dictionary keys
    people_dict = {p1: "First person", p2: "Second person"}
    print(f"Dictionary with people as keys: {people_dict}")

    # Lookup works as expected
    print(f"Looking up p1: {people_dict.get(p1)}")

    # Try to modify p1 after it's been used as a key
    try:
        p1.age = 26
        print(f"Modified p1: {p1}")  # This should not execute
    except TypeError as e:
        print(f"Exception when modifying p1: {e}")

    # Create a new person with the same values as original p1
    p3 = Person("Bob", 25)
    print(f"New person p3: {p3}")

    # Lookup with equivalent person works
    print(f"Looking up p3 (equivalent to original p1): {people_dict.get(p3)}")


def demonstrate_inherited_hash():
    """Demonstrate that inherited hash methods are accepted."""
    print("\n=== Inherited Hash Example ===")

    child = ChildWithInheritedHash(42)
    print(f"Created: {child}")

    child.value = 43  # This works before hash
    print(f"Modified before hash: {child}")

    h = hash(child)  # This will set hash_taken
    print(f"Hash value: {h}")

    try:
        child.value = 44
        print(f"Modified after hash: {child}")  # This should not execute
    except TypeError as e:
        print(f"Exception when modifying: {e}")


def demonstrate_hash_assertion():
    """Demonstrate the assertion error with a class that doesn't have __hash__."""
    print("\n=== Hash Assertion Example ===")

    try:
        # This will be executed at import time, so we need to define the class here
        # to avoid breaking the whole module if it fails
        exec("""
class NoHashClass:
    def __init__(self, value):
        self.value = value

# This should raise an AssertionError
lazy_freeze(NoHashClass)
        """)
    except AssertionError as e:
        print(f"Got expected AssertionError: {e}")

    # Show that even with __eq__, we still need __hash__
    try:
        exec("""
class HasEqButNoHash:
    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        if not isinstance(other, HasEqButNoHash):
            return False
        return self.value == other.value

# This should also raise an AssertionError
lazy_freeze(HasEqButNoHash)
        """)
    except AssertionError as e:
        print(f"Got expected AssertionError: {e}")


def demonstrate_inplace_operations():
    """Demonstrate protection against in-place operations."""
    print("\n=== In-place Operations Example ===")

    # Create a counter
    c = Counter(10)
    print(f"Created: {c}")

    # Modify before hash
    c += 5
    print(f"After c += 5: {c}")

    # Take the hash
    h = hash(c)
    print(f"Hash value: {h}")

    # Try in-place operations after hash
    try:
        c += 3
        print(f"After c += 3: {c}")  # This should not execute
    except TypeError as e:
        print(f"Exception when using +=: {e}")

    try:
        c -= 2
        print(f"After c -= 2: {c}")  # This should not execute
    except TypeError as e:
        print(f"Exception when using -=: {e}")


def demonstrate_deletion():
    """Demonstrate protection against attribute and item deletion."""
    print("\n=== Deletion Protection Example ===")

    # Create an attribute container
    container = AttributeContainer(name="Test", count=42)
    print(f"Created: {container}")
    print(f"Container items: {container.items}")

    # Delete before hash
    del container.count
    print(f"After deleting count attribute: {container}")

    del container["name"]
    print(f"After deleting 'name' item: {container.items}")

    # Take the hash
    h = hash(container)
    print(f"Hash value: {h}")

    # Try deletions after hash
    try:
        del container.name
        # This should not execute
        print(f"After deleting name attribute: {container}")
    except TypeError as e:
        print(f"Exception when deleting attribute: {e}")

    try:
        container.items["test"] = "value"  # Add an item
        del container["test"]
        # This should not execute
        print(f"After deleting 'test' item: {container.items}")
    except TypeError as e:
        print(f"Exception when deleting item: {e}")


# New demo for debug mode
def demonstrate_debug_mode():
    """Demonstrate debug mode with stack traces."""
    print("\n=== Debug Mode Example ===")

    # Create a debug person
    dp = DebugPerson("Debug", 99)
    print(f"Created: {dp}")

    # Modify before hash
    dp.age = 100
    print(f"Modified before hash: {dp}")

    # Take the hash via a separate function to create a more interesting stack trace
    print("Taking hash in a separate function...")
    h = hash_object(dp)
    print(f"Hash value: {h}")

    # Try to modify after hash via a separate function
    print("\nAttempting to modify after hash via separate function...")
    try:
        modify_object(dp)
    except TypeError as e:
        print("Exception when modifying:")
        print(e)


if __name__ == "__main__":
    demonstrate_person()
    demonstrate_dict()
    demonstrate_dict_usage()
    demonstrate_inherited_hash()
    demonstrate_hash_assertion()
    demonstrate_inplace_operations()
    demonstrate_deletion()
    demonstrate_debug_mode()  # New demo for debug mode
