import collections
import copy as dcopy

from typing import Iterator, Union, Any
from pathlib import Path

from . import core
from . import parser
from .types import Storage, Key, Keys

from pprint import pformat


class Safict(collections.Mapping):
    def __init__(
        self,
        storage: Storage = None,
        separator: str = None,
    ):
        self._storage = storage or {}
        self._original_storage = dcopy.deepcopy(self._storage)
        self.separator = separator

    def _split_keys(self, keys: Keys) -> Keys:
        _keys = []
        if self.separator is not None:
            for key in keys:
                if type(key) == str:
                    splits = key.split(self.separator)
                else:
                    splits = [key]
                for elem in splits:
                    _keys.append(elem)
        else:
            _keys = keys

        return _keys

    def get(self, *keys: Key, **get_params) -> Storage:
        """
        Getter for dict
        """
        _keys = self._split_keys(keys)
        result: Storage = core.get(self._storage, *_keys, **get_params)
        return result

    def to_dict(self) -> dict:
        return dcopy.deepcopy(self._storage)

    def set(self, *keys: Key, value, **set_params) -> 'Safict':
        _set_params = parser.update(dict(inplace=False), set_params)
        _keys = self._split_keys(keys)

        result: Storage = core.set(
            self._storage,
            *_keys, **_set_params,
            value=value
        )

        return Safict(result, separator=self.separator)

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

    def copy(self) -> 'Safict':
        """
        Creates a new copy of Safict
        Returns:
            (Safict): new copy
        """
        storage = dcopy.deepcopy(self._storage)
        result = Safict(storage, self.separator)

        return result

    def with_separator(self, separator: str = None) -> 'Safict':
        storage = dcopy.deepcopy(self._storage)
        result = Safict(storage, separator)

        return result

    def __copy__(self):
        return self.copy()

    def __getitem__(self, keys: Union[Key, Keys]) -> Storage:
        if type(keys) == tuple:
            result = self.get(*keys)
        else:
            result = self.get(keys)
        return result

    def __setitem__(self, keys: Union[Key, Keys], value: Any) -> None:
        if type(keys) == tuple:
            self.set(*keys, value=value, inplace=True)
        else:
            self.set(keys, value=value, inplace=True)

    def __len__(self) -> int:
        return self._storage.__len__()

    def __iter__(self) -> Iterator[Key]:
        return self._storage.__iter__()

    def __str__(self) -> str:
        storage = pformat(self._storage)
        result = f"Safict(\n" \
            f"\tseparator={self.separator}\n" \
            f"\tlength={self.__len__()}\n" \
            f"\tstorage={storage}\n)"
        return result

    def __repr__(self) -> str:
        result = self.__str__()
        return result
