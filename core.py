from typing import Any, Optional, Tuple, List, NamedTuple
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


class Result:
    def __init__(
            self,
            value: Optional[Storage],
            status: int,
            last_value: Optional[Storage],
            last_container: Optional[Storage],
            last_value_key_id: int,
            last_container_key_id: int
    ):
        self.value = value
        self.status = status
        self.last_value = last_value
        self.last_container = last_container
        self.last_value_key_id = last_value_key_id
        self.last_container_key_id = last_container_key_id


def _is_container(_storage: Storage) -> bool:
    return hasattr(_storage, '__setitem__')


def _make_container(_key: Key) -> Storage:
    if isinstance(_key, int):
        return [None] * _key
    else:
        return {_key: {}}


def _need_last_value_strategy(_status: int, _value: Optional[Any], _strategy: str) -> bool:
    check_strategy = _strategy == Strategy.LAST_VALUE
    check_status = _status != Status.OKAY or _value is None

    return check_strategy and check_status


def _need_last_container_strategy(_status: int, _value: Optional[Any], _strategy: str) -> bool:
    check_strategy = _strategy == Strategy.LAST_CONTAINER
    check_status = _status != Status.OKAY or _value is None

    return check_strategy


def _need_missing_key_strategy(_status: int, _value: Optional[Any], _strategy: str) -> bool:
    check_strategy = _strategy == Strategy.MISSING_KEY
    check_status = _status in Status.WRONG_KEY

    return check_strategy and check_status


def _need_default_strategy(_status: int, _value: Optional[Any], _strategy: str) -> bool:
    check_strategy = _strategy == Strategy.ON_FINAL
    return check_strategy and _value is None


def _need_transform(_status: int, _value: Optional[Any], transform: Optional[Transform]) -> bool:
    return (_value is not None) and (transform is not None)


def _get_value(_storage: Storage, _key: Optional[Key]) -> Tuple[int, Optional[Any]]:
    status: int = Status.OKAY
    result: Optional[Any] = None

    if _storage is None:
        return Status.STORAGE_IS_NONE, result

    if _key is None:
        return Status.KEY_IS_NONE, result

    if not (isinstance(_key, str) or isinstance(_key, int)):
        return Status.WRONG_KEY_TYPE, result

    if hasattr(_storage, '__getitem__'):
        if isinstance(_storage, list) and isinstance(_key, int):
            status = Status.OKAY if 0 <= _key < len(_storage) else Status.MISSING_KEY
        else:
            status = Status.OKAY if _key in _storage else Status.MISSING_KEY

        if status == Status.OKAY:
            try:
                value = _storage[_key]
                result = value
            except:
                status = Status.EXCEPTION_RAISED
    else:
        return Status.WRONG_STORAGE_TYPE, result

    return status, result


def _transform(_value: Any, transform: Transform):
    try:
        return transform(_value)
    except:
        return None


def __get(
        storage: Optional[Storage],
        *keys: Key
) -> Result:

    result = storage
    _status = Status.OKAY
    previous_value = result

    previous_container = {}

    last_value_key_id = 0
    last_container_key_id = 0

    if len(keys) == 0:
        _status, result = _get_value(storage, None)

    for i, key in enumerate(keys):
        if _status == Status.OKAY:
            _status, result = _get_value(result, key)
            if result is not None:
                previous_value = result
                last_value_key_id += 1

                if _is_container(result):
                    previous_container = result
                    last_container_key_id += 1
        else:
            break

    _result = Result(
        result,
        _status,
        previous_value,
        previous_container,
        last_value_key_id,
        last_container_key_id
    )
    return _result


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
    except:
        return Status.EXCEPTION_RAISED, None


def safe_get(
        storage: Optional[Storage],
        *keys: Key,
        strategy: str = "final",
        default: Optional[Any] = None,
        transform: Optional[Transform] = None
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
        :param transform:
            If not None, applies this type or function to the result
        :param default:
            Default value used for :strategy: param
        :return:
            Value or None
        """
    if strategy not in Strategy.ALL:
        raise ValueError(f'Strategy must be on of {Strategy.ALL}. Got {strategy}')

    result: Result = __get(storage, *keys)

    value = result.value
    status = result.status

    if _need_transform(status, value, transform):
        value = _transform(value, transform)

    if _need_last_container_strategy(status, value, strategy):
        value = result.last_container

    if _need_last_value_strategy(status, value, strategy):
        value = result.last_value

    if _need_missing_key_strategy(status, value, strategy) \
            or _need_default_strategy(status, value, strategy):
        value = default

    return value


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

    if not _is_container(_storage):
        key = keys[0]
        _storage = _make_container(key)

    result = __get(_storage, *keys)

    container = result.last_container
    unused_keys: List[Key] = list(keys[result.last_container_key_id:])

    previous_container = container
    for key in unused_keys:
        status, container = _inner_set(container, key, value)
        if status == Status.OKAY:
            previous_container = container
        else:
            container = _make_container(key)
            _inner_set(previous_container, key, container)

    return _storage

