from typing import Any, Optional, Tuple
import copy

from .types import Storage, Key, Apply


class Safitty:
    _STATUS_OKAY = 0
    _STATUS_STORAGE_IS_NONE = 1
    _STATUS_KEY_IS_NONE = 2
    _STATUS_MISSING_KEY = 3
    _STATUS_WRONG_KEY_TYPE = 4
    _STATUS_WRONG_STORAGE_TYPE = 5
    _STATUS_EXCEPTION_RAISED = 6

    _WRONG_KEY_STATUSES = [_STATUS_KEY_IS_NONE, _STATUS_MISSING_KEY, _STATUS_WRONG_KEY_TYPE]

    _STRATEGY_MISSING_KEY = "missing_key"
    _STRATEGY_ON_FINAL = "final"
    _STRATEGY_LAST_VALUE = "last_value"

    _ALL_STRATEGIES = [_STRATEGY_MISSING_KEY, _STRATEGY_ON_FINAL, _STRATEGY_LAST_VALUE]

    @staticmethod
    def _inner_get(_storage: Storage, _key: Optional[Key]) -> Tuple[int, Optional[Any]]:
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
    def _need_last_value_strategy(_status: int, _value: Optional[Any], _strategy: str) -> bool:
        check_strategy = _strategy == Safitty._STRATEGY_LAST_VALUE
        check_status = _status != Safitty._STATUS_OKAY or _value is None

        return check_strategy and check_status

    @staticmethod
    def _need_missing_key_strategy(_status: int, _value: Optional[Any], _strategy: str) -> bool:
        check_strategy = _strategy == Safitty._STRATEGY_MISSING_KEY
        check_status = _status in Safitty._WRONG_KEY_STATUSES

        return check_strategy and check_status

    @staticmethod
    def _need_default_strategy(_status: int, _value: Optional[Any], _strategy: str) -> bool:
        check_strategy = _strategy == Safitty._STRATEGY_ON_FINAL
        return check_strategy and _value is None

    @staticmethod
    def _need_apply(_status: int, _value: Optional[Any], apply: Optional[Apply]) -> bool:
        return (_value is not None) and (apply is not None)

    @staticmethod
    def _apply(_value: Any, apply: Apply):
        try:
            return apply(_value)
        except:
            return None

    @staticmethod
    def get(
            storage: Optional[Storage],
            *keys: Key,
            strategy: str = "final",
            default: Optional[Any] = None,
            apply: Optional[Apply] = None
    ) -> Optional[Any]:
        """
        Allows you to safely retrieve values from nested dictionaries of any depth.
        Examples:
            >>> import safitty as sf
            >>> config = {
                    "greetings": [
                        {"hello": "world"},
                        {"hi": "there"},
                    ],
                    "storage": { "some_string": "some_value" },
                    "status": 200
                }

            >>> sf.safe_get(config, "greetings",  1, "hi")
                "there"

            >>> sf.safe_get(config, "greetings", 0)
                {"hi": "there"}

            >>> sf.safe_get(config, "greetings",  2, "hi") # Note the wrong index
                None

            >>> sf.safe_get(config, "storage", "no", "key", "at", 1, "all", 4)
                None

            >>> sf.safe_get(config, "storage", "no", "key", "at", 1, "all", 4, default="It's safe and simple")
                It's safe and simple

            >>> NOT_FOUND = 404
            >>> sf.safe_get(config, "status", apply=lambda x: x != NOT_FOUND)
                True
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
        :param apply:
            If not None, applies this type or function to the result
        :return:
        """

        if strategy not in Safitty._ALL_STRATEGIES:
            raise ValueError(f'Strategy must be on of {Safitty._ALL_STRATEGIES}. Got {strategy}')

        result = storage
        _status = Safitty._STATUS_OKAY
        previous_value = result

        if len(keys) == 0:
            _status, result = Safitty._inner_get(storage, None)

        for i, key in enumerate(keys):
            if _status == Safitty._STATUS_OKAY:
                _status, result = Safitty._inner_get(result, key)
                if result is not None:
                    previous_value = result
            else:
                break

        if Safitty._need_apply(_status, result, apply):
            result = Safitty._apply(result, apply)

        if Safitty._need_last_value_strategy(_status, result, strategy):
            return previous_value

        if Safitty._need_missing_key_strategy(_status, result, strategy):
            return default

        if Safitty._need_default_strategy(_status, result, strategy):
            return default

        return result

    @staticmethod
    def _inner_set(
            _storage: Storage,
            value: Any,
            _key: Optional[Key],
            list_default: Any = None
    ) -> Tuple[int, Optional[Storage]]:
        if _storage is None:
            return Safitty._STATUS_STORAGE_IS_NONE, None

        if _key is None:
            return Safitty._STATUS_KEY_IS_NONE, None

        if not (isinstance(_key, str) or isinstance(_key, int)):
            return Safitty._STATUS_WRONG_KEY_TYPE, None

        if hasattr(_storage, '__setitem__'):
            if isinstance(_storage, list) and isinstance(_key, int):
                if 0 <= _key:
                    length = len(_storage)
                    if _key >= length:
                        extend_length = _key - length + 1
                        _storage.extend([list_default] * extend_length)
                else:
                    return Safitty._STATUS_MISSING_KEY, None

            try:
                _storage[_key] = value
                return Safitty._STATUS_OKAY, _storage
            except:
                return Safitty._STATUS_EXCEPTION_RAISED, None
        else:
            return Safitty._STATUS_WRONG_STORAGE_TYPE, None

    @staticmethod
    def set(
            storage: Optional[Storage],
            value: Any,
            *keys: Key,
            inplace: bool = False,
            strategy: str = 'none'
    ) -> Optional[Storage]:
        """

        :param storage:
        :param value:
        :param keys:
        :param strategy:
        :return:
        """
        _storage = copy.deepcopy(storage)
        _get_status = Safitty._STATUS_OKAY
        previous_value = _storage

        for key in keys:
            _set_status, _storage = Safitty._inner_set(previous_value, value, key)
            if _storage is not None:
                previous_value = _storage

        return _storage


def safe_get(
        storage: Optional[Storage],
        *keys: Key,
        strategy: str = "final",
        default: Optional[Any] = None,
        apply: Optional[Apply] = None
) -> Optional[Any]:
    return Safitty.get(storage, *keys, strategy=strategy, default=default, apply=apply)


def safe_set():
    pass
