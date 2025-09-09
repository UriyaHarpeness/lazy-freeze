# lazy-freeze

A Python decorator that makes objects immutable after their hash is calculated.

## Overview

`lazy-freeze` provides a simple solution to a common problem in Python: ensuring immutability of objects after they're used as dictionary keys. This is implemented as a decorator that makes objects behave normally until their hash is calculated, at which point they become immutable.

## Installation

Clone this repository:

```bash
git clone https://github.com/ofekshilon/lazy-freeze.git
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

### Selective Attribute Freeze

If your `__hash__` implementation only depends on certain attributes, you can selectively freeze only those attributes:

```python
@lazy_freeze(freeze_attrs=["name", "age"])
class PartiallyFrozenPerson:
    def __init__(self, name, age, description):
        self.name = name
        self.age = age
        self.description = description  # Not used in hash
        
    def __hash__(self):
        return hash((self.name, self.age))  # Only uses name and age
    
    def __eq__(self, other):
        if not isinstance(other, PartiallyFrozenPerson):
            return False
        return self.name == other.name and self.age == other.age

# Create and hash a person
p = PartiallyFrozenPerson("Alice", 30, "Software Engineer")
h = hash(p)

# Frozen attributes cannot be modified
try:
    p.name = "Bob"  # This will raise TypeError
except TypeError as e:
    print(f"Error: {e}")

# Non-frozen attributes can still be modified
p.description = "Senior Engineer"  # This works fine
```
