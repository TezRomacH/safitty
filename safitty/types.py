from typing import Dict, Union, List, Any, Type, Callable


class Relative:
    def __init__(self, pat: str = '*'):
        assert pat in ['*', '**']
        self.pat = pat

    def __str__(self) -> str:
        return self.pat

    def __repr__(self) -> str:
        return self.pat

    def __eq__(self, other: 'Relative') -> bool:
        return self.pat == other.pat


__relative_star = Relative('*')
__relative_dstar = Relative('**')


def star():
    return __relative_star


def dstar():
    return __relative_dstar


Storage = Union[Dict[str, Any], List[Any]]
Key = Union[str, int, bool, Relative]

Transform = Union[Type, Callable]

