import collections
import copy as dcopy
from typing import Iterator, Union, Tuple
from pathlib import Path
from .types import Storage, Key

from . import core
from . import parser


class Safict(collections.Mapping):
    def __init__(
        self,
        storage: Storage = None,
        separator=None,
    ):
        self._storage = storage or {}
        self.separator = separator

    def get(self, *keys: Key, **get_params) -> Storage:
        _keys = []
        if self.separator is not None:
            for key in keys:
                split = key.split(self.separator)
                for elem in split:
                    _keys.append(elem)
        else:
            _keys = keys

        result: Storage = core.get(self._storage, *_keys, **get_params)
        return result

    def to_dict(self) -> dict:
        return dcopy.deepcopy(self._storage)

    def set(self, *keys: Key, value, **set_params) -> 'Safict':
        result: Storage = core.set(
            self._storage,
            *keys, **set_params,
            value=value, inplace=False
        )

        return Safict(result)

    @staticmethod
    def load(
        path: Union[str, Path],
        ordered: bool = False,
        encoding: str = "utf-8"
    ) -> 'Safict':
        result: Storage = parser.load(path, ordered=ordered, encoding=encoding)

        return Safict(result)

    def save(
        self,
        path: Union[str, Path],
        encoding: str = "utf-8",
        ensure_ascii: bool = False,
        indent: int = 2,
    ) -> None:
        parser.save(
            self._storage,
            path=path,
            encoding=encoding,
            ensure_ascii=ensure_ascii,
            indent=indent,
        )

    def copy(self, separator=None) -> 'Safict':
        storage = dcopy.deepcopy(self._storage)
        result = Safict(storage, separator)

        return result

    def __copy__(self, separator=None):
        return self.copy(separator)

    def __getitem__(self, keys: Union[Key, Tuple[Key, ...]]) -> Storage:
        if type(keys) == tuple:
            result = self.get(*keys)
        else:
            result = self.get(keys)
        return result

    def __len__(self) -> int:
        return self._storage.__len__()

    def __iter__(self) -> Iterator[Key]:
        return self._storage.__iter__()

