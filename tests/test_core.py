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


def test_safe_get(config):
    assert safitty.safe_get(config) == config
    assert isinstance(safitty.safe_get(config, "words"), dict)
    assert safitty.safe_get(config, "words", "one") == "uno"
    assert safitty.safe_get(config, "words", "one", "two") is None
    assert safitty.safe_get(config, "words", "one", "two", default="hi") == "hi"
    assert safitty.safe_get(config, "words", "none") is None
    assert safitty.safe_get(config, "words", "none", default=42) == 42

    assert safitty.safe_get(config, "key") is not None
    assert safitty.safe_get(config, "key", 0) is None
    assert safitty.safe_get(config) is not None
    assert safitty.safe_get(config, "keyu", default="value") == "value"
    assert safitty.safe_get(config, "key", "value", 0) is not None
    assert safitty.safe_get(config, "key", "value", 0) == "elem1"
    assert safitty.safe_get(config, "key", "value", 1) == "elem2"
    assert safitty.safe_get(config, "key", "value", 2) is None
    assert safitty.safe_get(config, "key", "value", 2, default="elem2") == "elem2"
    assert safitty.safe_get(config, "key", "value", 2, "deep", 1, 1, "other", default="elem2") == "elem2"
    assert safitty.safe_get(config, None) is None
    assert safitty.safe_get(config, None, default=True)


def test_safe_get_strategies(config):
    assert safitty.safe_get(
        config, "key", "value", "elem1", strategy="last_container") == ["elem1", "elem2"]
    assert safitty.safe_get(config, "key", "value", 1, "bad", strategy="last_value") == "elem2"
    assert safitty.safe_get(
        config, "key", "value", 1, "bad", strategy="last_value", default="not_elem2") == "elem2"
    assert safitty.safe_get(
        config, "key", "value", 3, "bad", strategy="last_value", default="not_elem2") == ["elem1", "elem2"]

    assert safitty.safe_get(config, "words", "none") is None
    assert safitty.safe_get(config, "words", "none", default=42, strategy="missing_key") != 42
    assert safitty.safe_get(config, "words", "none", default=42, strategy="missing_key") is None


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
    main_client: Client = safitty.safe_get(config, "servers", "main-server", apply=Client)
    assert type(main_client) == Client
    assert main_client.address == "localhost:8888"
    assert main_client.password == "qwerty"
    assert safitty.safe_get(
        config, "servers", "main-server", transform=lambda x: Client(**x)) == main_client

    assert safitty.safe_get(config, "servers", "broken-server", apply=Client) is None

    with pytest.raises(TypeError):
        safitty.safe_get(config, "servers", "broken-server", apply=Client, raise_on_transforms=True)

    with_default: Client = safitty.safe_get(config, "servers", "with-default-pass", apply=Client)
    assert with_default is not None
    assert with_default.address == "https://github.com/TezRomacH/safitty"
    assert with_default.address == safitty.safe_get(config, "servers", "with-default-pass", "address")
    assert with_default.password == "12345"
    assert safitty.safe_get(config, "servers", "with-default-pass", "password") is None

    assert safitty.safe_get(config, "numbers", apply=sum_args) == 12
    with pytest.raises(TypeError):
        safitty.safe_get(config, "numbers", transform=sum_args, raise_on_transforms=True)

    assert safitty.safe_get(config, "numbers", transform=lambda x: sum_args(*x)) == 12

    status_bad_request = safitty.safe_get(config, "status", transform=lambda x: x == 400)
    assert type(status_bad_request) == bool
    assert status_bad_request


def test_safe_set(config):
    config = copy.deepcopy(config)
    assert safitty.safe_get(config, "numbers", transform=len) == 5
    safitty.safe_set(config, "numbers", 8, value=42)
    assert safitty.safe_get(config, "numbers", transform=len) == 9
    assert safitty.safe_get(config, "numbers", 8) == 42

    assert safitty.safe_set(config, "numbers2", "inner", value=[])
    assert safitty.safe_get(config, "numbers2", "inner", transform=len) == 0
    assert safitty.safe_set(config, "numbers", value=[])
    assert safitty.safe_get(config, "numbers", transform=len) == 0
