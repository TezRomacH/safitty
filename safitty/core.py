from typing import Any, Optional, Tuple, List, Type, Dict
import copy

from .types import Storage, Key, Transform


class Status:
    OKAY = 0
    STORAGE_IS_NONE = 1
    KEY_IS_NONE = 2
    MISSING_KEY = 3
    WRONG_KEY_TYPE = 4
    WRONG_STORAGE_TYPE = 5
    EXCEPTION_RAISED = 6

    WRONG_KEY = [KEY_IS_NONE, MISSING_KEY, WRONG_KEY_TYPE]
    
    
class Strategy:
    MISSING_KEY = "missing_key"
    ON_FINAL = "final"
    LAST_VALUE = "last_value"
    LAST_CONTAINER = "last_container"
    
    ALL = [MISSING_KEY, ON_FINAL, LAST_VALUE, LAST_CONTAINER]

# Checkers


def is_container(storage: Storage) -> bool:
    return hasattr(storage, '__setitem__')


def make_container(key: Key) -> Storage:
    if isinstance(key, int):
        return [None] * key
    else:
        return {key: {}}


def need_last_value(status: int, value: Optional[Any], strategy: str) -> bool:
    check_strategy = strategy == Strategy.LAST_VALUE
    check_status = status != Status.OKAY or value is None

    return check_strategy and check_status


def need_default(status: int, value: Optional[Any], strategy: str) -> bool:
    strategy_final = (strategy == Strategy.ON_FINAL) and value is None
    strategy_missing_key = (strategy == Strategy.MISSING_KEY) and (status in Status.WRONG_KEY)

    return strategy_final or strategy_missing_key


def need_apply_function(value: Optional[Any], function: Optional[Transform]) -> bool:
    return (value is not None) and (function is not None)

# Getters


def get_value(storage: Storage, key: Optional[Key]) -> Tuple[int, Optional[Any]]:
    if storage is None:
        return Status.STORAGE_IS_NONE, None

    if key is None:
        return Status.KEY_IS_NONE, storage

    if not (isinstance(key, str) or isinstance(key, int) or isinstance(key, bool)):
        return Status.WRONG_KEY_TYPE, storage

    status: int = Status.OKAY
    result: Optional[Any] = None

    if hasattr(storage, '__getitem__'):
        if (isinstance(storage, list) or isinstance(storage, tuple)) and isinstance(key, int):
            status = Status.OKAY if 0 <= key < len(storage) else Status.MISSING_KEY
        else:
            status = Status.OKAY if key in storage else Status.MISSING_KEY

        if status == Status.OKAY:
            try:
                value = storage[key]
                result = value
            except Exception:
                status = Status.EXCEPTION_RAISED
    else:
        return Status.WRONG_STORAGE_TYPE, result

    return status, result


def get_by_keys(
        storage: Optional[Storage],
        *keys: Key
) -> Dict[str, Any]:

    value = storage
    status = Status.OKAY
    last_value = value

    last_container = {}

    last_value_key_id = 0
    last_container_key_id = 0

    if len(keys) == 0:
        status, value = get_value(storage, None)

    for i, key in enumerate(keys):
        if status == Status.OKAY:
            status, value = get_value(value, key)
            if value is not None:
                last_value = value
                last_value_key_id += 1

                if is_container(value):
                    last_container = value
                    last_container_key_id += 1
        else:
            break

    result = {
        "value": value,
        "status": status,

        "last_value": last_value,
        "last_value_key_id": last_value_key_id,

        "last_container": last_container,
        "last_container_key_id": last_container_key_id
    }
    return result


def safe_get(
        storage: Optional[Storage],
        *keys: Key,
        strategy: str = "final",
        default: Optional[Any] = None,
        transform: Optional[Transform] = None,
        apply: Optional[Type] = None
) -> Optional[Any]:
    """
        Allows you to safely retrieve values from nested dictionaries of any depth.
        Examples:
            >>> import safitty as sf
            config = {
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
            >>> sf.safe_get(config, "status", transform=lambda x: x != NOT_FOUND)
                True
        :param storage:
            Dictionary or list with nested dictionaries. Usually it's a configuration file (yaml of json)
        :param keys:
            Keys for the storage, Must be int or str
        :param keys:
            Various number of keys or indexes
        :param strategy:
            Must be one of
                - final: Returns a default value if the final result is None
                - missing_key: Returns a default value only is some of the keys is missing
                - last_value: Returns last available nested value. It doesn't use `default` param
        :param default:
            Default value used for :strategy: param
        :param transform:
            If not None, applies this type or function to the result
        :param apply:
            As ``transform`` the parameter applies the result but unpacks it
            (pass ``*result`` to a function/type  if ``result`` is a list
            or **result if ``result`` is a dict)
        :return:
            Value or None
        """
    if strategy not in Strategy.ALL:
        raise ValueError(f'Strategy must be on of {Strategy.ALL}. Got {strategy}')

    result = get_by_keys(storage, *keys)

    value = result['value']
    status = result['status']

    if strategy == Strategy.LAST_CONTAINER:
        value = result["last_container"]

    if need_last_value(status, value, strategy):
        value = result["last_value"]

    if need_default(status, value, strategy):
        value = default

    try:
        if need_apply_function(value, apply):
            if isinstance(value, list):
                value = apply(*value)
            elif isinstance(value, dict):
                value = apply(**value)

        elif need_apply_function(value, transform):
            value = transform(value)
    except Exception:
        pass

    return value

# Setters


def _inner_set(
        _storage: Storage,
        _key: Optional[Key],
        value: Any,
        list_default: Any = None
) -> Tuple[int, Optional[Storage]]:
    if _storage is None:
        return Status.STORAGE_IS_NONE, None

    if _key is None:
        return Status.KEY_IS_NONE, None

    if not (isinstance(_key, str) or isinstance(_key, int)):
        return Status.WRONG_KEY_TYPE, None

    if isinstance(_storage, list) and isinstance(_key, int):
        if 0 <= _key:
            length = len(_storage)
            if _key >= length:
                extend_length = _key - length + 1
                _storage.extend([list_default] * extend_length)
        else:
            return Status.MISSING_KEY, None

    try:
        _storage[_key] = value
        return Status.OKAY, _storage
    except Exception:
        return Status.EXCEPTION_RAISED, None


def safe_set(
        storage: Optional[Storage],
        *keys: Key,
        value: Any,
        inplace: bool = False,
        strategy: str = 'none'
) -> Optional[Storage]:
    """

    :param storage:
    :param keys:
    :param value:
    :param inplace:
    :param strategy:
    :return:
    """
    if len(keys) == 0:
        return storage

    _storage = copy.deepcopy(storage)

    if not is_container(_storage):
        key = keys[0]
        _storage = make_container(key)

    result = get_by_keys(_storage, *keys)

    container = result["last_container"]
    unused_keys: List[Key] = list(keys[result["last_container_key_id"]:])

    previous_container = container
    for key in unused_keys:
        status, container = _inner_set(container, key, value)
        if status == Status.OKAY:
            previous_container = container
        else:
            container = make_container(key)
            _inner_set(previous_container, key, container)

    return _storage

