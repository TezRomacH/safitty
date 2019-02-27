import copy
import pytest
import safitty


@pytest.fixture(scope="module")
def config(request):
    configuration = {
        "words": {
            "one": "uno",
            "two": "dos",
            "three": "tres",
            "none": None
        },
        "key": {
            "value": ["elem1", "elem2"]
        },
        "servers": {
            "main-server": {
                "address": "localhost:8888",
                "password": "qwerty"
            },

            "broken-server": {
                "password": "42"  # no address
            },

            "with-default-pass": {
                "address": "https://github.com/TezRomacH/safitty"
            },
            "other": None
        },
        "numbers": [1, 2, -2, 4, 7],
        "numbers2": {
            "inner": [-1, -2]
        },
        "status": 400
    }
    return configuration


@pytest.fixture(scope="module")
def transforms(request):
    transforms = [
        {
            'name': 'Normalize',
            'function': 'ToTensor',
            'params': None
        },
        {
            'name': 'Padding',
            'function': 'Pad',
            'params': {
                'fill': 3,
                'padding_mode': 'reflect'
            }
        }
    ]

    return transforms


def test_safe_get(config):
    assert safitty.get(config) == config
    assert isinstance(safitty.get(config, "words"), dict)
    assert safitty.get(config, "words", "one") == "uno"
    assert safitty.get(config, "words", "one", "two") is None
    assert safitty.get(config, "words", "one", "two", default="hi") == "hi"
    assert safitty.get(config, "words", "none") is None
    assert safitty.get(config, "words", "none", default=42) == 42

    assert safitty.get(config, "key") is not None
    assert safitty.get(config, "key", 0) is None
    assert safitty.get(config) is not None
    assert safitty.get(config, "keyu", default="value") == "value"
    assert safitty.get(config, "key", "value", 0) is not None
    assert safitty.get(config, "key", "value", 0) == "elem1"
    assert safitty.get(config, "key", "value", 1) == "elem2"
    assert safitty.get(config, "key", "value", 2) is None
    assert safitty.get(config, "key", "value", 2, default="elem2") == "elem2"
    assert safitty.get(config, "key", "value", 2, "deep", 1, 1, "other", default="elem2") == "elem2"
    assert safitty.get(config, None) is None
    assert safitty.get(config, None, default=True)


def test_safe_get_strategies(config):
    assert safitty.get(
        config, "key", "value", "elem1", strategy="last_container") == ["elem1", "elem2"]
    assert safitty.get(config, "key", "value", 1, "bad", strategy="last_value") == "elem2"
    assert safitty.get(
        config, "key", "value", 1, "bad", strategy="last_value", default="not_elem2") == "elem2"
    assert safitty.get(
        config, "key", "value", 3, "bad", strategy="last_value", default="not_elem2") == ["elem1", "elem2"]

    assert safitty.get(config, "words", "none") is None
    assert safitty.get(config, "words", "none", default=42, strategy="missing_key") != 42
    assert safitty.get(config, "words", "none", default=42, strategy="missing_key") is None


class Client:
    def __init__(self, address: str, password: str = "12345"):
        self.address = address
        self.password = password

    def __eq__(self, other: 'Client'):
        types = type(other) == Client
        addresses = self.address == other.address
        passwords = self.password == other.password

        return types and addresses and passwords


def sum_args(*args):
    result = 0
    for arg in args:
        result += arg
    return result


def test_safe_get_transformations(config):
    main_client: Client = safitty.get(config, "servers", "main-server", apply=Client)
    assert type(main_client) == Client
    assert main_client.address == "localhost:8888"
    assert main_client.password == "qwerty"
    assert safitty.get(
        config, "servers", "main-server", transform=lambda x: Client(**x)) == main_client

    assert safitty.get(config, "servers", "broken-server", apply=Client) is None

    with pytest.raises(TypeError):
        safitty.get(config, "servers", "broken-server", apply=Client, raise_on_transforms=True)

    with_default: Client = safitty.get(config, "servers", "with-default-pass", apply=Client)
    assert with_default is not None
    assert with_default.address == "https://github.com/TezRomacH/safitty"
    assert with_default.address == safitty.get(config, "servers", "with-default-pass", "address")
    assert with_default.password == "12345"
    assert safitty.get(config, "servers", "with-default-pass", "password") is None

    assert safitty.get(config, "numbers", apply=sum_args) == 12
    with pytest.raises(TypeError):
        safitty.get(config, "numbers", transform=sum_args, raise_on_transforms=True)

    assert safitty.get(config, "numbers", transform=lambda x: sum_args(*x)) == 12

    status_bad_request = safitty.get(config, "status", transform=lambda x: x == 400)
    assert type(status_bad_request) == bool
    assert status_bad_request


def test_safe_set(config):
    config = copy.deepcopy(config)
    assert safitty.get(config, "numbers", transform=len) == 5
    safitty.set(config, "numbers", 8, value=42)
    assert safitty.get(config, "numbers", transform=len) == 9
    assert safitty.get(config, "numbers", 8) == 42

    assert safitty.set(config, "numbers2", "inner", value=[])
    assert safitty.get(config, "numbers2", "inner", transform=len) == 0
    assert safitty.set(config, "numbers", value=[])
    assert safitty.get(config, "numbers", transform=len) == 0


def test_safe_set_strategies(config):
    config = copy.deepcopy(config)
    safitty.set(config, "words", "quadre", value="four", strategy="existing_key")
    assert safitty.get(config, "words", "quadre") is None

    safitty.set(config, "words", "one", value="four", strategy="existing_key")
    assert safitty.get(config, "words", "one") is not None
    assert safitty.get(config, "words", "one") == "four"

    safitty.set(config, "words", "one", value="five", strategy="missing_key")
    assert safitty.get(config, "words", "one") != "five"

    safitty.set(config, "words", "five", value="five", strategy="missing_key")
    assert safitty.get(config, "words", "five") == "five"

    # cannot reset a reference
    assert safitty.set(config, value="hi") == "hi"
    assert config != "hi"

    safitty.set(config, "numbers", 40, "hi", "", value="привет")
    assert safitty.get(config, "numbers", 40, "hi", "") is not None
    assert safitty.get(config, "numbers", 40, "hi", "") == "привет"


def test_safe_set_2(transforms):
    transforms = copy.deepcopy(transforms)
    safitty.set(transforms, 2, "name", value="BatchNorm2d")
    assert safitty.get(transforms, 2, "name") == "BatchNorm2d"

    safitty.set(transforms, 1, "params", value="add", strategy="on_none")
    params1 = safitty.get(transforms, 1, "params")
    assert params1 is not None
    assert params1 != "add"

    safitty.set(transforms, 0, "params", value="subtract", strategy="on_none")
    params0 = safitty.get(transforms, 0, "params")
    assert params0 is not None
    assert params0 == "subtract"
