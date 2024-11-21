Map a Nested JSON Key Path to a Field
=====================================

This feature allows mapping nested JSON paths to individual dataclass fields using a custom object path notation. It supports both ``Annotated`` types and ``dataclasses.Field`` for flexibility in how you map JSON data to dataclass fields.

### Basic Usage Example
------------------------

Here’s an example that demonstrates how to define and use nested key paths for JSON deserialization. It uses both the `Annotated` type with `KeyPath` and `path_field`.

```python
from dataclasses import dataclass
from dataclass_wizard import JSONWizard, KeyPath, path_field
from typing import Annotated

@dataclass
class Example(JSONWizard):
    # Use Annotated with KeyPath for nested JSON path mapping
    an_int: Annotated[int, KeyPath('data.nested.int')]
    # Use path_field to map to a nested JSON path with a default value
    my_str: str = path_field(['metadata', 'info', 'name'], default='unknown')
```

- The field ``an_int`` maps to the nested JSON path ``data.nested.int``.
- The field ``my_str`` uses ``path_field`` to map to the path ``metadata.info.name``, with a default value of ``'unknown'`` if not found in the JSON data.

### Expanded Example with JSON
-------------------------------

Given the following JSON data:

```json
{
    "data": {
        "nested": {
            "int": 42
        }
    },
    "metadata": {
        "info": {
            "name": "John Doe"
        }
    }
}
```

Deserializing the JSON with the `from_dict` method:

```python
example = Example.from_dict({
    "data": {
        "nested": {
            "int": 42
        }
    },
    "metadata": {
        "info": {
            "name": "John Doe"
        }
    }
})
print(example.an_int)  # 42
print(example.my_str)  # 'John Doe'
```

This shows how the JSON data is mapped to the dataclass fields using the custom key paths.

### Object Path Breakdown
--------------------------

The object path notation used in `KeyPath` and `path_field` is parsed as follows:

- **Dot (`.`) notation** is used to separate nested object keys.
- **Square brackets (`[]`)** are used to access array elements by index.
- **Quotes (`"`)** around keys or values indicate they are to be treated as strings, and are only necessary when keys or values contain spaces, special characters, or otherwise cannot be parsed as standard identifiers.

#### Example 1: Simple Path
```python
split_object_path('data[info][name]')
```

Output:
```
['data', 'info', 'name']
```
- This represents the path to access the `name` field inside the `info` object, which is nested inside the `data` object.

#### Example 2: Integer Path
```python
split_object_path('data[5].value')
```

Output:
```
['data', 5, 'value']
```
- The path `data[5].value` accesses the `value` field inside the sixth item (index 5) of the `data` array.

#### Example 3: Boolean Path
```python
split_object_path('user[isActive]')
```

Output:
```
['user', 'isActive']
```
- The path `user[isActive]` accesses the boolean field `isActive` inside the `user` object. Note that `isActive` is a boolean here.

#### Example 4: Floats in Path
```python
split_object_path('data[0.25]')
```

Output:
```
['data', 0.25]
```
- The path `data[0.25]` is used to access the value at index `0.25`. In practice, this would be an error, as array indices are integers. This example illustrates how floats are parsed as float types.

#### Example 5: Strings in Path (Without Quotes)
```python
split_object_path('data[user_name]')
```

Output:
```
['data', 'user_name']
```
- The path `data[user_name]` accesses the field `user_name` inside the `data` object. Note that `user_name` is treated as a string even though it's not wrapped in quotes. This is because it's a valid identifier without spaces or special characters.

#### Example 6: Strings in Path (With Quotes)
```python
split_object_path('data["user name"]')
```

Output:
```
['data', 'user name']
```
- The path `data["user name"]` accesses the field `user name` inside the `data` object. Here, the quotes are necessary because `user name` contains a space, which would otherwise cause parsing issues.

#### Example 7: Mixed Types in Path
```python
split_object_path('data[0]["user name"].info["age"]')
```

Output:
```
['data', 0, 'user name', 'info', 'age']
```
- This path accesses the `age` field inside the `info` object, which is inside the `user name` object at index `0` of the `data` array. The `user name` key is treated as a string due to the space, while `0` is an integer.

### Handling Quotes in Object Path
--------------------------

When values in the object path are wrapped in quotes, they are treated as strings. This is useful when your JSON keys or indices contain special characters or spaces that would otherwise cause parsing errors.

#### Example 1: Wrapped in Quotes for String Interpretation
```python
split_object_path('data["user name"].age')
```

Output:
```
['data', 'user name', 'age']
```
- Here, `"user name"` is treated as a string with a space, which is essential if your JSON key contains spaces or special characters.

#### Example 2: Nested Array Indices as String
```python
split_object_path('data["myList"][2]["value"]')
```

Output:
```
['data', 'myList', 2, 'value']
```
- In this case, `2` is an integer index in the array `myList`, and `"value"` is a string key inside the array item.

### Best Practices
--------------

- Use **`Annotated`** with **`KeyPath`** for specifying complex, nested object paths for dataclass fields.
- Use **`path_field`** for more flexible mapping with the ability to set defaults or customize serialization behavior.
- Keep object paths simple and clear, especially when wrapping values in quotes, to ensure they are correctly interpreted as strings.
