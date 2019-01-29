# Safitty
[![Pipi version](https://img.shields.io/pypi/v/safitty.svg)](https://pypi.org/project/safitty/)
[![License](https://img.shields.io/github/license/TezRomacH/safitty.svg)](LICENSE)]

Safitty is a wrapper on JSON/YAML configs for Python.
Designed with a focus on the security of `get`/`set` operations for deep-nested dictionaries and lists.

## Installation
```bash
pip install safitty
```

## Features
- Safe `get` for dictionaries and lists
- Nested keys at one time
- Several strategies 

## Usage

Suppose you have a configuration file looks like:

```yaml
verbose: false

status: 1

paths:
  jsons:
    - first
    - second
    - third
  images: important/path/to/images/
  
transforms:
  - name: Normalize
    function: ToTensor
    params: null
  -
    name: Padding
    function: Pad
    params:
      fill: 3
      padding_mode: reflect
```
Maybe it's located at your project folder or you receive it from a server.
For now we want to load the config and get some of the nested keys 
```python
import safitty as sf
import yaml


with open("path/to/config.yml") as stream:
    config = yaml.load(stream)
    
param = sf.safe_get(config, 'paths', 'images')
# param == 'important/path/to/images/'
```

Python's dict will throw an error if we try to get a non-existing path. Or it will turn into a disgusting construction.
```python
# usual way to work with dict

>>> config['transforms'][1]['param']['fill'] # oops, we wrote `param` insted of `params
KeyError: 'param'

>>> config.get('transforms')[1].get('param').get('fill') # What if we go deeeeeeper
AttributeError: 'NoneType' object has no attribute 'get'

>>> config.get('transforms')[1].get('params').get('fill') # it works, but looks awful
3
``` 

Anyway this last way doesn't help us with lists. Standard Python library doesn't provide safe `get` method for type `list` 
```python
>>> config.get('transforms')[2].get('params').get('fill') # wrong index
IndexError: list index out of range
```

Solution here is to use Saffity:
```python
>>> sf.safe_get(config, 'transforms', 2, 'params', 'fill')
# None

>>> sf.safe_get(config, 'transforms', 1, 'params', 'fill')
3

>>> sf.safe_get(config, 'transforms', 2, 'values', 'fill', default=42)
42
```

With Safitty you'll not be scared about nested depth
```python
>>> sf.safe_get(config, 'transforms', 1, 'params', 'fill', 'what', 'if', 'we', 'go', 'deeper')
# None

>>> sf.safe_get(config, 'transforms', 3, "wrong_key", 55, 'params', 'go', 'deeper', default="This is default value")
This is default value
```

Safitty provides several strategies for using the `default` param.
```python
>>> sf.safe_get(config, 'transforms', 0, 'values', strategy='missing_key', default=42)
42

>>> sf.safe_get(config 'transforms', 0, 'values', strategy='last_value', default=42)
{"name": "Normalize", "function": "ToTensor", "params": None}
```
1. For strategy `final`, it returns `default` if the final result on applying keys is None. Safitty uses it by default
1. For strategy `missing_key`, it returns `default` only if some key in keys doesn't exist in config.
1. Strategy `last_value` returns last non null value if exists
1. Strategy `last_container` returns last non null container if exists

Note the difference for `final` and `missing_key` strategies.
```python
>>> sf.safe_get(config, 'transforms', 0, 'params', default='No value')
No value

>>> sf.safe_get(config, 'transforms', 0, 'params', strategy='missing_key', default='No value')
# return None, because there were not not-existing keys

# But if we make a mistake in keys 
>>> sf.safe_get(config, 'transforms', 23, 'params', strategy='missing_key', default='No value')
No value

# or
>>> sf.safe_get(config, 'transforms', 0, 'values', strategy='missing_key', default='No value')
No value

```

Saffity provides `transform` params. If it's not `None`, the result will be applied to this type or function.

```python
>>> from pathlib import Path
>>> sf.safe_get(config, 'paths', 'images', transform=Path)
PosixPath('important/path/to/images/')

```

```python
>>> sf.safe_get(config, 'status', transform=bool)
True

```

Lambdas are also supported

```python
NOT_FOUND = 404
>>> sf.safe_get(config, 'status', transform=lambda x: x != NOT_FOUND)

True

```

With `transform` you can easily initialize your class from config

```python

transform = sf.safe_get(
    config, 'transforms', 0,
    default={},
    transform = lambda params: YourAmazingClass(**params)
    )

```

More advanced
```python
import safitty as sf

augmentations = []

for transform in sf.safe_get(config, 'transforms', default=[]):
    function = ALL_FUNCTIONS[sf.safe_get(transform, 'name', default="Identity")]
    
    aug = sf.safe_get(transform, 'params', default={}, transform=function)
    
    augmentations.append(aug)
```

