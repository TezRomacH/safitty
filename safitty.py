from typing import Any, Optional, Dict, Union, List, Tuple


Storage = Union[Dict[str, Any], List[Any]]


class Safitty:
    _STATUS_NULL = -1
    _STATUS_OKAY = 0
    _STATUS_STORAGE_IS_NONE = 1
    _STATUS_KEY_IS_NONE = 2
    _STATUS_MISSING_KEY = 3
    _STATUS_WRONG_KEY_TYPE = 4
    _STATUS_WRONG_STORAGE_TYPE = 5
    _STATUS_EXCEPTION_RAISED = 6

    _STRATEGY_MISSING_KEY = "missing_key"
    _STRATEGY_ON_FINAL = "final"
    _STRATEGY_LAST_VALUE = "last_value"

    _ALL_STRATEGIES = [_STRATEGY_MISSING_KEY, _STRATEGY_ON_FINAL, _STRATEGY_LAST_VALUE]

    @staticmethod
    def _inner_get(_storage: Storage, _key: Union[str, int]) -> Tuple[int, Optional[Any]]:
        status: int = Safitty._STATUS_OKAY
        result: Optional[Any] = None

        if _storage is None:
            return Safitty._STATUS_STORAGE_IS_NONE, result

        if _key is None:
            return Safitty._STATUS_KEY_IS_NONE, result

        if not (isinstance(_key, str) or isinstance(_key, int)):
            return Safitty._STATUS_WRONG_KEY_TYPE, result

        if hasattr(_storage, '__getitem__'):
            if isinstance(_storage, list) and isinstance(_key, int):
                status = Safitty._STATUS_OKAY if 0 <= _key < len(_storage) else Safitty._STATUS_MISSING_KEY
            else:
                status = Safitty._STATUS_OKAY if _key in _storage else Safitty._STATUS_MISSING_KEY

            if status == Safitty._STATUS_OKAY:
                try:
                    value = _storage[_key]
                    result = value
                except:
                    status = Safitty._STATUS_EXCEPTION_RAISED
        else:
            return Safitty._STATUS_WRONG_STORAGE_TYPE, result

        return status, result

    @staticmethod
    def get(
            storage: Optional[Storage],
            key: Union[str, int],
            *keys: Union[str, int],
            strategy: str = "final",
            default: Optional[Any] = None
    ) -> Optional[Any]:
        """
        Allows you to safely retrieve values from nested dictionaries of any depth.
        Examples:
            >>> config = {
                "top": {
                    "nested_1": [
                        {"hello": "world"},
                        {"hi": "there"},
                    ],
                    "nested_2": { "some_string": "some_value" }
                }}

            >>> Safitty.get(config, "nested_1",  1, "hi")
                "there"

            >>> Safitty.get(config, "nested_1", 0)
                {"hi": "there"}

            >>>  Safitty.get(config, "nested_1",  2, "hi")
                None

            >>> Safitty.get(config, "nested_2", "no", "key", "at", 1, "all", 4)
                None
        :param storage:
            Dictionary or list with nested dictionaries. Usually it's a configuration file (yaml of json)
        :param key:
            At least one key must be set
        :param keys:
            Various number of keys or indexes
        :param strategy:
            Must be one of
                - final: Returns a default value if the final result is None
                - missing_key: Returns a default value only is some of the keys is missing
                - last_value: Returns last available nested value. It doesn't use `default` param
        :param default:
            Default value used for :strategy: param
        :return:
        """

        if strategy not in Safitty._ALL_STRATEGIES:
            raise ValueError(f'Strategy must be on of {Safitty._ALL_STRATEGIES}. Got {strategy}')

        keys = [key] + list(keys)

        value = storage
        _status = Safitty._STATUS_OKAY
        previous_value = value
        for key in keys:
            if _status == Safitty._STATUS_OKAY:
                _status, value = Safitty._inner_get(value, key)
                if value is not None:
                    previous_value = value
            else:
                break

        if _status != Safitty._STATUS_OKAY and strategy == Safitty._STRATEGY_LAST_VALUE:
            return previous_value

        if _status == Safitty._STATUS_MISSING_KEY and strategy == Safitty._STRATEGY_MISSING_KEY:
            return default

        if value is None and strategy == Safitty._STRATEGY_ON_FINAL:
            return default

        return value
