import mprop

from safitty.core import safe_get
from safitty.types import Storage, Key, Transform


class __relative:
    def __init__(self, pat: str = '*'):
        assert pat in ['*', '**']
        self.pat = pat

    def __str__(self) -> str:
        return self.pat

    def __repr__(self) -> str:
        return self.pat

    def __eq__(self, other: '__relative') -> bool:
        return self.pat == other.pat


__relative_star = __relative('*')
__relative_dstar = __relative('**')


@mprop.mproperty
def star(self):
    return __relative('*')


@mprop.mproperty
def dstar(self):
    return __relative('**')


__all__ = ["safe_get", "star", "dstar", "Storage", "Key", "Transform"]
