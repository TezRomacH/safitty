# Safitty
[![Build Status](https://travis-ci.com/catalyst-team/safitty.svg?branch=master)](https://travis-ci.com/catalyst-team/safitty)
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
- Multiple keys at one `get`/`set` call.
- Several strategies, includes: Get the most deep non-null value by your keys, Get the last non-null container and more
- Value transformations to classes

## Quickstart

```python
import safitty

# Loads config YAML or JSON
config = safitty.load("/path/to/config.yml")

# Getting value from the config
safitty.get(config, "very", "deep", "call", default="This is the default value")

# Setting value into
safitty.set(config, "clients", 0, "address", value="localhost:8888")
```

More examples in the [getting-started notebook](examples/getting_started.ipynb).