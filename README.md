# lazy-freeze

A Python decorator that makes objects immutable after their hash is calculated.

## Overview

`lazy-freeze` provides a simple solution to a common problem in Python: ensuring immutability of objects after they're used as dictionary keys. This is implemented as a decorator that makes objects behave normally until their hash is calculated, at which point they become immutable.

## Installation

Clone this repository:

```bash
git clone https://github.com/username/lazy-freeze.git
cd lazy-freeze
```

## Usage

### Basic Usage

```python
from lazy_freeze import lazy_freeze

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

# Create a person
p = Person("Alice", 30)

# Modify before hash - this works fine
p.age = 31

# Take the hash - this freezes the object
h = hash(p)

# Try to modify after hash - this raises TypeError
try:
    p.age = 32
except TypeError as e:
    print(f"Error: {e}")  # Error: Cannot modify Person after its hash has been taken
```

### Debug Mode

Enable debug mode to capture stack traces when an object's hash is taken:

```python
@lazy_freeze(debug=True)
class DebugPerson:
    def __init__(self, name, age):
        self.name = name
        self.age = age
        
    def __hash__(self):
        return hash((self.name, self.age))

# Create and hash a person
p = DebugPerson("Alice", 30)
h = hash(p)

# Attempting to modify will show where the hash was calculated
try:
    p.age = 32
except TypeError as e:
    print(f"Error:\n{e}")
    # Output will include the stack trace from when hash(p) was called
```

## Features

- **Lazy immutability**: Objects remain mutable until their hash is calculated
- **Complete protection**: Blocks attribute and item modification, deletion, and in-place operations
- **Preserves original behavior**: Respects any custom `__hash__` implementation
- **Works with dictionary-like objects**: Supports classes that implement `__setitem__` and `__delitem__`
- **Debug mode**: Captures stack traces to help identify where objects were hashed
- **Inherited hash support**: Works with classes that inherit a hash method from a parent

## Why Use lazy-freeze?

In Python, objects used as dictionary keys should not change in ways that would affect their hash value. If they do, they can become "lost" in dictionaries. This decorator provides a safety mechanism that automatically prevents such modifications after an object has been hashed.

## Examples

See the `examples.py` file for complete usage examples.

## License

This project is licensed under the terms of the included LICENSE file.
