from typing import Dict, Union, List, Any, Type, Callable


class Relative:
    def __init__(self, pat: str = "*"):
        assert pat in ["*", "**"]
        self.pat = pat

    def __str__(self) -> str:
        return self.pat

    def __repr__(self) -> str:
        return self.pat

    def __eq__(self, other: 'Relative') -> bool:
        return self.pat == other.pat


__relative_star = Relative("*")
__relative_dstar = Relative("**")


def star():
    return __relative_star


def dstar():
    return __relative_dstar


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
    LAST_VALUE = "last_value"
    LAST_CONTAINER = "last_container"
    FORCE = "force"
    EXISTING_KEY = "existing_key"

    ALL_FOR_GET = [FORCE, MISSING_KEY, LAST_VALUE, LAST_CONTAINER]
    ALL_FOR_SET = [FORCE, MISSING_KEY, EXISTING_KEY]


Storage = Union[Dict[str, Any], List[Any]]
Key = Union[str, int, bool, Relative]

Transform = Union[Type, Callable]
