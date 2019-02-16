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

# If there is no specific key for `config` dict it returns the `default` 
safitty.safe_get(config, "very", "deep", "call", default="This is the default value")

safitty.safe_set(config, "clients", 0, "address", value="localhost:8888")
```


