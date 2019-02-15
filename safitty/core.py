import copy
from typing import Optional, Tuple

from .types import *


# Checkers
def is_container(storage: Storage) -> bool:
    return hasattr(storage, "__setitem__")


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
    relatives: List[Relative] = []

    previous_is_key: bool = False
    current_is_dstar: bool = False
    for key in keys:
        if isinstance(key, Relative):
            if previous_is_key and current_is_dstar:
                continue
            if key == star():
                relatives.append(key)
            elif key == dstar():
                current_is_dstar = True
                relatives = [key]

            previous_is_key = True
        else:
            if previous_is_key:
                previous_is_key = False
                current_is_dstar = False
                result += relatives
                relatives = []
            result.append(key)

    return result

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

    if hasattr(storage, "__getitem__"):
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

    last_container = storage

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
        apply: Optional[Transform] = None
) -> Optional[Any]:
    """Getter for nested dictionaries/lists of any depth.
    Args:
        storage (Storage): The container for `get`. Usually it's a configuration file (yaml of json)
        *keys (Key):  Keys for the storage, param list of int or str
        strategy (str): Must be one of
            - final: Returns a default value if the final result is None
            - missing_key: Returns a default value only is some of the keys is missing
            - last_value: Returns last available nested value. It doesn't use `default` param
            - last_container:
        default (Any):  Default value used for :strategy: param
        transform (Transform): Either type or a function.
            If this parameter is not None then applies it to the result value
        apply (Transform): As ``transform`` the parameter applies the result but unpacks it
            (pass ``*result`` to a function/type  if ``result`` is a list
            or **result if ``result`` is a dict)
    Returns:
            Any: The result value or ``default``
        """
    if strategy not in Strategy.ALL_FOR_GET:
        raise ValueError(f"Strategy must be on of {Strategy.ALL_FOR_GET}. Got {strategy}")

    keys = reformat_keys(keys)
    result = get_by_keys(storage, *keys)

    value = result["value"]
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

    return value


# Setters
def extend_container(container, key) -> Status:
    if isinstance(container, list):
        if isinstance(key, int):
            length = len(container)
            if key > length:
                container.extend([None] * (key - length + 1))
            return Status.OKAY
        else:
            return Status.WRONG_KEY_TYPE

    return Status.OKAY


def set_into_container(container, current_key, next_key) -> Tuple[Status, Optional[Storage]]:
    if isinstance(next_key, int):
        default = [None] * (next_key + 1)
    elif isinstance(next_key, str):
        default = dict()
    else:
        return Status.WRONG_KEY_TYPE, None

    try:
        container[current_key] = default
        return Status.OKAY, container[current_key]
    except Exception:
        return Status.EXCEPTION_RAISED, None


def safe_set(
        storage: Optional[Storage],
        *keys: Key,
        value: Any,
        inplace: bool = True
) -> Optional[Storage]:
    """Setter for nested dictionaries/lists of any depth
    Args:
        storage (Storage): The container that set into. Usually it's a configuration file (yaml of json)
        *keys (Key):  Keys for the storage, param list of int or str
        value (Any): The value to set into the storage
        inplace (bool): If True set value inplace into the storage, otherwise don't change the ``storage``
            params, returns only updated
    Returns:
        Storage: updated storage
    """
    if len(keys) == 0:
        return value

    if inplace:
        updated_storage = storage
    else:
        updated_storage = copy.deepcopy(storage)
    result = get_by_keys(updated_storage, *keys)

    last_container_key_id = result['last_container_key_id']
    unused_keys = list(keys[last_container_key_id:])
    container = result['last_container']

    i = 0
    is_okay = True
    while i < len(unused_keys) - 1:
        key = unused_keys[i]
        next_key = unused_keys[i+1]
        can_change = extend_container(container, key)
        if can_change != Status.OKAY:
            is_okay = False
            break
        can_update, next_container = set_into_container(container, key, next_key)

        if can_update != Status.OKAY:
            is_okay = False
            break
        else:
            container = next_container

        i += 1

    if is_okay:
        key = unused_keys[-1]
        container[key] = value

    return updated_storage

