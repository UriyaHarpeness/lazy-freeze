from __future__ import annotations

import unittest

import pytest
from typing_extensions import Self

from lazy_freeze import lazy_freeze


class TestLazyFreeze(unittest.TestCase):
    """Test cases for the lazy_freeze decorator."""

    def test_basic_functionality(self) -> None:
        """Test that objects can be modified before hash but not after."""

        @lazy_freeze
        class Person:
            def __init__(self, name: str, age: int) -> None:
                self.name = name
                self.age = age

            def __hash__(self) -> int:
                return hash((self.name, self.age))

            def __eq__(self, other: object) -> bool:
                if not isinstance(other, Person):
                    return False
                return self.name == other.name and self.age == other.age

        # Create a person and modify before hash
        p = Person("Alice", 30)
        p.age = 31  # This should work
        assert p.age == 31
        print(p.__dict__)

        # Take the hash
        hash(p)
        print(p.__dict__)

        # Try to modify after hash
        with pytest.raises(RuntimeError):
            p.age = 32

    def test_debug_mode(self) -> None:
        """Test that debug mode captures stack trace."""

        @lazy_freeze(debug=True)
        class Person:
            def __init__(self, name: str, age: int) -> None:
                self.name = name
                self.age = age

            def __hash__(self) -> int:
                return hash((self.name, self.age))

        # Create a person and hash it
        p = Person("Bob", 25)
        hash(p)

        assert hasattr(p, "__lazy_freeze_hash_stack_trace")

        # Try to modify
        try:
            p.age = 26
            self.fail("Should have raised RuntimeError")
        except RuntimeError as e:
            # Error message should contain stack trace
            assert "Hash was calculated at:" in str(e)

    def test_deletion_protection(self) -> None:
        """Test that attribute and item deletion are prevented after hash."""

        @lazy_freeze
        class Container(dict):
            def __init__(self, **kwargs: object) -> None:
                super().__init__(**kwargs)
                self.name: str | None = None
                self.value: int | None = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

            def __hash__(self) -> int:  # type: ignore
                return hash(tuple(sorted(self.items())))

        # Create container and modify before hash
        c = Container(name="Test", value=42)
        c["extra"] = "data"
        del c["extra"]  # This should work

        # Take the hash
        hash(c)

        # Try to delete attribute after hash
        with pytest.raises(RuntimeError):
            del c.name

        # Try to delete item after hash
        with pytest.raises(RuntimeError):
            del c["value"]

    def test_inplace_operations(self) -> None:
        """Test that in-place operations are prevented after hash."""

        @lazy_freeze
        class Counter:
            def __init__(self, value: int = 0) -> None:
                self.value: int = value

            def __hash__(self) -> int:
                return hash(self.value)

            def __iadd__(self, other: int) -> Self:
                self.value += other
                return self

            def __isub__(self, other: int) -> Self:
                self.value -= other
                return self

        # Create counter and modify before hash
        c = Counter(10)
        c += 5  # This should work
        assert c.value == 15

        # Take the hash
        hash(c)

        # Try in-place operations after hash
        with pytest.raises(RuntimeError):
            c += 3

        with pytest.raises(RuntimeError):
            c -= 2

    def test_non_class_application(self) -> None:
        """Test that applying the decorator to a non-class entity raises TypeError."""

        # Define a simple function
        def sample_function(x):
            return x * 2

        # Try to apply lazy_freeze to the function
        with pytest.raises(TypeError) as context:
            lazy_freeze(sample_function)  # type: ignore

        # Check that the error message is as expected
        error_message = str(context.value)
        assert "@lazy_freeze can only be applied to classes" in error_message
        assert "is of type 'function'" in error_message

        # Test with a non-function, non-class entity
        with pytest.raises(TypeError) as context:
            lazy_freeze(42)  # type: ignore

        # Check error message for non-function
        error_message = str(context.value)
        assert "@lazy_freeze can only be applied to classes" in error_message
        assert "is of type 'int'" in error_message

    def test_freeze_attributes(self) -> None:
        """Test that only specified attributes are frozen when using freeze_attrs."""

        @lazy_freeze(freeze_attrs=frozenset({"name", "age"}))
        class PartialPerson:
            def __init__(self, name: str, age: int, description: str) -> None:
                self.name = name
                self.age = age
                self.description = description  # Not used in hash

            def __hash__(self) -> int:
                return hash((self.name, self.age))  # Only uses name and age

            def __eq__(self, other: object) -> bool:
                if not isinstance(other, PartialPerson):
                    return False
                return self.name == other.name and self.age == other.age

        # Create a person
        p = PartialPerson("Alice", 30, "Software Engineer")

        # Take the hash
        hash(p)

        # Try to modify protected attributes (should raise RuntimeError)
        with pytest.raises(RuntimeError):
            p.name = "Bob"

        with pytest.raises(RuntimeError):
            p.age = 31

        # Try to modify unprotected attribute (should work)
        p.description = "Senior Software Engineer"
        assert p.description == "Senior Software Engineer"

    def test_freeze_attributes_2(self) -> None:
        """Test that only specified attributes are frozen when using freeze_attrs."""

        @lazy_freeze(freeze_attrs=frozenset({"name", "age"}))
        class PartialPerson:
            def __init__(self, name: str, age: int, description: str) -> None:
                self.name = name
                self.age = age
                self.description = description  # Not used in hash

            def __hash__(self) -> int:
                if self.name == "Alice":
                    return hash((self.name, self.age))
                return hash((self.name, self.description))

            def __eq__(self, other: object) -> bool:
                if not isinstance(other, PartialPerson):
                    return False
                return self.name == other.name and self.age == other.age

        # Create a person
        p = PartialPerson("Alice", 30, "Software Engineer")
        p2 = PartialPerson("Bob", 30, "Software Engineer")

        # Take the hash
        print(p.__dict__)

        hash(p)
        hash(p2)

        print(p.__dict__)

        # Try to modify protected attributes (should raise RuntimeError)
        with pytest.raises(RuntimeError):
            p.name = "Bob"

        with pytest.raises(RuntimeError):
            p.age = 31

        # Try to modify unprotected attribute (should work)
        p.description = "Senior Software Engineer"
        assert p.description == "Senior Software Engineer"

    def test_freeze_attributes_3(self) -> None:
        """Test that only specified attributes are frozen when using freeze_attrs."""

        @lazy_freeze(freeze_attrs="dynamic")
        class PartialPerson:
            def __init__(self, name: str, age: int, description: str) -> None:
                self.name = name
                self.age = age
                self.description = description  # Not used in hash

            def __hash__(self) -> int:
                if self.name == "Alice":
                    return hash((self.name, self.age))
                return hash((self.name, self.description))

            def __eq__(self, other: object) -> bool:
                if not isinstance(other, PartialPerson):
                    return False
                return self.name == other.name and self.age == other.age

        # Create a person
        p = PartialPerson("Alice", 30, "Software Engineer")
        p2 = PartialPerson("Bob", 30, "Software Engineer")

        # Take the hash
        print(p.__dict__)

        hash(p)
        hash(p2)

        print(p.__dict__)

        # Try to modify protected attributes (should raise RuntimeError)
        with pytest.raises(RuntimeError):
            p.name = "Bob"

        with pytest.raises(RuntimeError):
            p.age = 31

        # Try to modify unprotected attribute (should work)
        p.description = "Senior Software Engineer"
        assert p.description == "Senior Software Engineer"

    def test_freeze_attributes_4(self) -> None:
        """Test that only specified attributes are frozen when using freeze_attrs."""

        @lazy_freeze(freeze_attrs="dynamic", cache_hash=True)
        class PartialPerson:
            def __init__(self, name: str, age: int, description: str) -> None:
                self.name = name
                self.age = age
                self.description = description  # Not used in hash

            def __hash__(self) -> int:
                if self.name == "Alice":
                    return hash((self.name, self.age))
                return hash((self.name, self.description))

            def __eq__(self, other: object) -> bool:
                if not isinstance(other, PartialPerson):
                    return False
                return self.name == other.name and self.age == other.age

        # Create a person
        p = PartialPerson("Alice", 30, "Software Engineer")
        p2 = PartialPerson("Bob", 30, "Software Engineer")

        # Take the hash
        print(p.__dict__)

        hash(p)
        hash(p2)
        hash(p2)

        print(p.__dict__)

        # Try to modify protected attributes (should raise RuntimeError)
        with pytest.raises(RuntimeError):
            p.name = "Bob"

        with pytest.raises(RuntimeError):
            p.age = 31

        # Try to modify unprotected attribute (should work)
        p.description = "Senior Software Engineer"
        assert p.description == "Senior Software Engineer"


if __name__ == "__main__":
    unittest.main()
