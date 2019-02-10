from typing import Optional, Tuple, List, Any, Type

from .types import star, Storage, Transform, Key, Relative


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


def key_is_correct(key: Key) -> bool:
    return isinstance(key, str) \
           or isinstance(key, int) \
           or isinstance(key, bool) \
           or isinstance(key, Relative)


def reformat_keys(keys: List[Key]) -> List[Key]:
    result: List[Key] = []
    current_relative: Relative = None

    previous_is_key: bool = False
    for key in keys:
        if isinstance(key, Relative):
            previous_is_key = True

            if current_relative is not None:
                current_relative = current_relative.merge(key)
            else:
                current_relative = key
        else:
            if previous_is_key:
                result.append(current_relative)
                current_relative = None
                previous_is_key = False
            result.append(key)

    flatten = []
    for key in result:
        if isinstance(key, Relative) and key == star():
            for i in range(key.depth):
                flatten.append(star())
        else:
            flatten.append(key)

    return flatten

# Getters


def get_value(storage: Storage, key: Optional[Key]) -> Tuple[int, Optional[Any]]:
    if storage is None:
        return Status.STORAGE_IS_NONE, None

    if key is None:
        return Status.KEY_IS_NONE, storage

    if not key_is_correct(key):
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
        storage: Storage,
        keys: List[Key],
        i_key: int = 0,
        prev_value = None,
        prev_container = None
) -> List[Any]:
    def make_result(status_, result_):
        result_dict = {
            "depth": i_key,
            "status": status_,
            "result": result_,

            "prev_value": prev_value,
            "prev_container": prev_container
        }
        return [result_dict]

    if i_key > len(keys):
        return make_result(-1, None)

    if i_key == len(keys):
        return make_result(0, storage)

    key = keys[i_key]

    result = []
    if isinstance(key, Relative) and key == star():
        inner_keys = []
        if isinstance(storage, list) or isinstance(storage, tuple):
            inner_keys = range(len(storage))
        elif isinstance(storage, dict):
            inner_keys = [key for key in storage]

        temp_ = [get_by_keys(storage[inner_key], keys, i_key + 1) for inner_key in inner_keys]
        temp_ = [t for t in temp_ if t != []]

        for t in temp_:
            t_dict = t[0]
            if t_dict['status'] == Status.OKAY:
                if t_dict['depth'] + 2 > len(keys):
                    result += t
                else:
                    result += get_by_keys(t_dict['result'], keys, i_key + 2)
            else:
                result += make_result(-1, None)

    else:
        status, value = get_value(storage, key)
        if status == Status.OKAY:
            result += get_by_keys(value, keys, i_key + 1)
        else:
            result += make_result(-1, None)

    return result


def safe_get(
        storage: Optional[Storage],
        *keys: Key,
        strategy: str = "final",
        default: Optional[Any] = None,
        transform: Optional[Transform] = None,
        apply: Optional[Type] = None,
        allow_multi_result: bool = False
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

    keys = reformat_keys(keys)
    results = get_by_keys(storage, keys)

    okay_result = [res for res in results if res['status'] == Status.OKAY]
    if len(okay_result) > 0:
        results = okay_result
    else:
        pass

    values = []
    for result in results:
        value = result["result"]
        status = result["status"]

        if strategy == Strategy.LAST_CONTAINER:
            value = result["last_container"]

        if need_last_value(status, value, strategy):
            value = result["last_value"]

        if need_default(status, value, strategy):
            value = default

        try:
            if need_apply_function(value, apply):
                if isinstance(value, list) or isinstance(value, tuple):
                    value = apply(*value)
                elif isinstance(value, dict):
                    value = apply(**value)
                else:
                    value = apply(value)

            elif need_apply_function(value, transform):
                value = transform(value)
        except Exception:
            pass

        values.append(value)

    if not allow_multi_result:
        values = values[0]

    return values
