import copy
from typing import Optional, Tuple, Any, List, Dict

from safitty.types import Storage, Status, Strategy, \
    Transform, Key, Relative, \
    star, dstar


# Checkers
def is_container(storage: Storage) -> bool:
    return hasattr(storage, "__setitem__")


def need_last_value(status: int, value: Optional[Any], strategy: str) -> bool:
    check_strategy = strategy == Strategy.LAST_VALUE
    check_status = status != Status.OKAY or value is None

    return check_strategy and check_status


def need_default(status: int, value: Optional[Any], strategy: str) -> bool:
    strategy_force = (strategy == Strategy.FORCE) and value is None
    strategy_missing_key = (strategy == Strategy.MISSING_KEY) and (status in Status.WRONG_KEY)

    return strategy_force or strategy_missing_key


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
        return Status.KEY_IS_NONE, None

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
        status, value = Status.OKAY, storage

    previous_container = None
    for i, key in enumerate(keys):
        if status == Status.OKAY:
            status, value = get_value(value, key)
            if value is not None:
                last_value = value
                last_value_key_id += 1

                if is_container(value):
                    previous_container = last_container
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
        "last_container_key_id": last_container_key_id,

        "previous_container": previous_container
    }
    return result


def safe_get(
        storage: Optional[Storage],
        *keys: Key,
        strategy: str = "force",
        default: Optional[Any] = None,
        transform: Optional[Transform] = None,
        apply: Optional[Transform] = None,
        raise_on_transforms: bool = False
) -> Optional[Any]:
    """Getter for nested dictionaries/lists of any depth.
    Args:
        storage (Storage): The container for `get`. Usually it's a configuration file (yaml of json)
        *keys (Key):  Keys for the storage, param list of int or str
        strategy (str): Must be one of
            - "force": Returns a default value if the final result is None
            - "missing_key": Returns a default value only is some of the keys is missing
            - "last_value": Returns last non null value. It doesn't use `default` param
            - "last_container": Returns last non-null container. It doesn't use `default` param
        default (Any):  Default value used for :strategy: param
        transform (Transform): Either type or a function.
            If this parameter is not None then applies it to the result value
        apply (Transform): As ``transform`` the parameter applies the result but unpacks it
            (pass ``*result`` to a function/type  if ``result`` is a list
            or **result if ``result`` is a dict)
        raise_on_transforms (bool): if set as True raise an Exception after fail on ``transforms`` or ``apply``
    Returns:
            Any: The result value or ``default``
        """
    if strategy not in Strategy.ALL_FOR_GET:
        raise ValueError(f"Strategy must be on of {Strategy.ALL_FOR_GET}. Got '{strategy}'")

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
        if raise_on_transforms:
            raise
        else:
            value = None

    return value


# Setters
def extend_container(container, key) -> Status:
    if isinstance(container, list):
        if isinstance(key, int):
            length = len(container)
            if key >= length:
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


def not_need_missing_key(on_missing_key: bool, strategy: str) -> bool:
    return (not on_missing_key) and strategy == Strategy.MISSING_KEY


def not_need_set_existing_key(on_existing_key: bool, strategy: str) -> bool:
    return (not on_existing_key) and strategy == Strategy.EXISTING_KEY


def safe_set(
        storage: Optional[Storage],
        *keys: Key,
        value: Any,
        strategy: str = "force",
        inplace: bool = True
) -> Optional[Storage]:
    """Setter for nested dictionaries/lists of any depth
    Args:
        storage (Storage): The container that set into. Usually it's a configuration file (yaml of json)
        *keys (Key):  Keys for the storage, param list of int or str
        value (Any): The value to set into the storage
        strategy (str): Setting strategy
            - "force" sets value anyway. If there were not such keys it creates them
            - "missing_key" sets value only if at some level a key were not in storage
            - "existing_key" sets value only if all key were in storage
        inplace (bool): If True set value inplace into the storage, otherwise don't change the ``storage``
            params, returns only updated
    Returns:
        Storage: updated storage
    """
    if len(keys) == 0:
        return value

    if strategy not in Strategy.ALL_FOR_SET:
        raise ValueError(f"Strategy must be on of {Strategy.ALL_FOR_SET}. Got '{strategy}'")

    if inplace:
        updated_storage = storage
    else:
        updated_storage = copy.deepcopy(storage)
    result = get_by_keys(updated_storage, *keys)

    last_container_key_id = result['last_container_key_id']
    unused_keys = list(keys[last_container_key_id:])
    container = result['last_container']

    on_existing_key = False
    on_missing_key = True
    count_unused = len(unused_keys)

    if count_unused == 0:
        unused_keys = [keys[-1]]
        container = result["previous_container"]
        on_existing_key = True
        on_missing_key = False
    elif count_unused == 1:
        item = unused_keys[0]
        in_container = item in container
        on_existing_key = in_container
        on_missing_key = not in_container

    i = 0
    is_okay = True

    if not_need_missing_key(on_missing_key, strategy) \
            or not_need_set_existing_key(on_existing_key, strategy):
        return updated_storage

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
        can_change = extend_container(container, key)
        if can_change == Status.OKAY:
            container[key] = value

    return updated_storage
