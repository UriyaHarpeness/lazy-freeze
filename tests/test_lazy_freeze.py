"""
Tests for the lazy_freeze decorator.
"""

import unittest
from lazy_freeze import lazy_freeze


class TestLazyFreeze(unittest.TestCase):
    """Test cases for the lazy_freeze decorator."""

    def test_basic_functionality(self):
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
        self.assertEqual(p.age, 31)

        # Take the hash
        h = hash(p)

        # Try to modify after hash
        with self.assertRaises(TypeError):
            p.age = 32

    def test_debug_mode(self) -> None:
        """Test that debug mode captures stack trace."""
        @lazy_freeze(debug=True)
        class Person:
            def __init__(self, name: str, age: int) -> None:
                self.name = name
                self.age = age
                self._hash_stack_trace: str = None

            def __hash__(self) -> int:
                return hash((self.name, self.age))

        # Create a person and hash it
        p = Person("Bob", 25)
        h = hash(p)

        # Check that _hash_stack_trace is set
        self.assertTrue(hasattr(p, '_hash_stack_trace'))

        # Try to modify
        try:
            p.age = 26
            self.fail("Should have raised TypeError")
        except TypeError as e:
            # Error message should contain stack trace
            self.assertIn("Hash was calculated at:", str(e))

    def test_deletion_protection(self):
        """Test that attribute and item deletion are prevented after hash."""
        @lazy_freeze
        class Container(dict):
            def __init__(self, **kwargs: object):
                super().__init__(**kwargs)
                self.name: str = None
                self.value: int = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

            def __hash__(self) -> int:
                return hash(tuple(sorted(self.items())))

        # Create container and modify before hash
        c = Container(name="Test", value=42)
        c["extra"] = "data"
        del c["extra"]  # This should work

        # Take the hash
        h = hash(c)

        # Try to delete attribute after hash
        with self.assertRaises(TypeError):
            del c.name

        # Try to delete item after hash
        with self.assertRaises(TypeError):
            del c["value"]

    def test_inplace_operations(self):
        """Test that in-place operations are prevented after hash."""
        @lazy_freeze
        class Counter:
            def __init__(self, value: int = 0):
                self.value: int = value

            def __hash__(self) -> int:
                return hash(self.value)

            def __iadd__(self, other: int) -> 'Counter':
                self.value += other
                return self

            def __isub__(self, other: int) -> 'Counter':
                self.value -= other
                return self

        # Create counter and modify before hash
        c = Counter(10)
        c += 5  # This should work
        self.assertEqual(c.value, 15)

        # Take the hash
        h = hash(c)

        # Try in-place operations after hash
        with self.assertRaises(TypeError):
            c += 3

        with self.assertRaises(TypeError):
            c -= 2


if __name__ == '__main__':
    unittest.main()
