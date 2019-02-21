# Safitty
[![Build Status](https://travis-ci.com/TezRomacH/safitty.svg?branch=master)](https://travis-ci.com/TezRomacH/safitty)
[![Pypi version](https://img.shields.io/pypi/v/safitty.svg?colorB=blue)](https://pypi.org/project/safitty/)
[![Downloads](https://img.shields.io/pypi/dm/safitty.svg?style=flat)](https://pypi.org/project/safitty/)
[![License](https://img.shields.io/github/license/TezRomacH/safitty.svg)](LICENSE)

Safitty is a wrapper on JSON/YAML configs for Python.
Designed with a focus on the safe `get`/`set` operations for deep-nested dictionaries and lists.

## Installation
```bash
pip install -U safitty
```

## Features
- Safe `get` for dictionaries and lists
- Safe `set` for dictionaries and lists
- Multiple keys at one `getter`/`setter` call.
- Several strategies, includes: Get the most deep non-null value by your keys, Get the last non-null container and more
- Value transformations to classes

## Quickstart

```python
import safitty

# Loads config YAML or JSON
config = safitty.load_config("/path/to/config.yml")

# Getting value from the config
safitty.safe_get(config, "very", "deep", "call", default="This is the default value")

# Setting value into
safitty.safe_set(config, "clients", 0, "address", value="localhost:8888")
```

## Why do I need **Safitty**?
When you work with big and deep configs or API it's getting difficult to safely take and proccess values.

Imagine you have a YAML-file looks like code below and you want to read the first function's name
```yaml
transforms:  
 - name: Normalize  
   function: ToTensor  
   params: null  
 
 - name: Padding  
   function: Pad  
   params:
	  fill: 3  
      padding_mode: reflect
```

It is really complicated to check all for None like
```python
import yaml
with open(config_path) as stream:
	config = yaml.load(stream)

result = config.get("transforms")
if result is not None:
	result = result[0]
	if result is not None:
		result = result.get("function")

if result is None:
	result = "identity"
```

Note that Python has no safe-method for lists, so if transforms were empty `result = result[0]` will raise an Exception. To avoid this, the code should be wrapped into `try: ... except: ...`

Safitty allows to do the same in more readable way
```python
import yaml
import safitty

# can load json or yaml
config = safitty.load_config(config_path)

# getter for any depth
result = safitty.safe_get(config, "transforms", 0, "function", default="identity")
```

For reverse action there is `safe_set`, method for setting value for any depth
```python
# this expand inner list to fit length of 2 and set {'name': 'BatchNorm2d'}
safitty.safe_set(config, "transforms", 2, "name", default="BatchNorm2d")
```
