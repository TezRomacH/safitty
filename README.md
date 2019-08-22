<div align="center">

![Safitty logo](https://raw.githubusercontent.com/catalyst-team/catalyst-pics/master/pics/safitty_logo.png)

[![Build Status](https://travis-ci.com/catalyst-team/safitty.svg?branch=master)](https://travis-ci.com/catalyst-team/safitty)
[![Pypi version](https://img.shields.io/pypi/v/safitty.svg?colorB=blue)](https://pypi.org/project/safitty/)
[![Downloads](https://img.shields.io/pypi/dm/safitty.svg?style=flat)](https://pypi.org/project/safitty/)
[![License](https://img.shields.io/github/license/TezRomacH/safitty.svg)](LICENSE)

[![Telegram](./pics/telegram.svg)](https://t.me/catalyst_team)
[![Gitter](https://badges.gitter.im/catalyst-team/community.svg)](https://gitter.im/catalyst-team/community?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge)
[![Slack](./pics/slack.svg)](https://opendatascience.slack.com/messages/CGK4KQBHD)
[![Donate](https://ucde0995747f356870f615ffb990.previews.dropboxusercontent.com/p/thumb/AAju2yA3zKEEfV1Rbe1hdCK94o5cVH5blrqQCBfy1BFudg8VfehnZrvBCpKEKUjZ0yce8rVWsXDlxCV2tmXL1f18h9VMod21hbQ-E7_X_Qbomca3PLeTe0pTgcfqs1gGef9JBs4y36-raLf2Qrkf_AJGdvUWscUd9OScOHYI8FyrjmF6pqVaMRnJGv8hmfg1QiT1ZjF2I1KqFMiDNxY3CvVltWNYnCltOk0mLG95yUBNlzJIOROCujlKRV1nAsoL6u7f_ynoVJBVmLsnTZeJ4izf10zCdGc5vmxxMRBTxxwZV4OPDuA7jlTfxB2983Ho5h0CzRGa3k6HwWsLmVUfU2Prno8-6UT99q2x3Lq2RXWaT8CbJe7FNg1LbI1WQWq-6_9oQA4JAOXjP_mbWXk721kz/p.png?fv_content=true&size_mode=5)](https://www.patreon.com/catalyst_team)

</div>

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