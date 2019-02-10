from typing import Dict, Union, List, Any, Type, Callable


class Relative:
    def __init__(self, pattern: str = '*', depth: int = 1):
        if pattern == '*' and depth < 1:
            raise Exception(f"For '*' wildcard depth must be >= 1")
        elif pattern == '**':
            depth = 1
        elif pattern not in ['*', '**']:
            raise Exception(f"Wrong pattern {pattern}")

        self.pattern: str = pattern
        self.depth: int = depth

    def __str__(self) -> str:
        if self.pattern == '*':
            return f"*{self.depth}"
        return self.pattern

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other: 'Relative') -> bool:
        return self.pattern == other.pattern

    def merge(self, other: 'Relative'):
        if self.pattern == "**" or other.pattern == "**":
            return Relative('**')
        else:
            return Relative('*', self.depth + other.depth)


def star(depth: int = 1):
    return Relative('*', depth)


def dstar():
    return Relative('**')


Storage = Union[Dict[str, Any], List[Any]]
Key = Union[str, int, bool, Relative]

Transform = Union[Type, Callable]

