# flake8: noqa
import pytest
import safitty


def test_safe_get():
    config = {
        "stages": {
            "one": "uno",
            "two": "dos",
            "three": "tres"
        },
        "key": {
            "value": "key2"
        }
    }

    assert safitty.safe_get(config) == config
    assert isinstance(safitty.safe_get(config, "stages"), dict)
    assert safitty.safe_get(config, "stages", "one") == "uno"
    assert safitty.safe_get(config, "stages", "one", "two") is None
    assert safitty.safe_get(config, "stages", "one", "two", default="hi") == "hi"

    assert safitty.safe_get(config, "key") is not None
