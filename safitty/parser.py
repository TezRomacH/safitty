"""
These functions are originally located at `Catalyst. Reproducible and fast DL & RL`_

Some methods were formatted and simplified.

.. _`Catalyst. Reproducible and fast DL & RL`:
    https://github.com/catalyst-team/catalyst
"""
import argparse
import copy
import json
import re
import warnings
from collections import OrderedDict
from pathlib import Path
from pydoc import locate
from typing import List, Any, Type, Optional, Union

import yaml

import safitty
from .types import Storage


def argparser(**argparser_kwargs) -> argparse.ArgumentParser:
    """Creates typical argument parser with ``--config`` argument
    Args:
        **argparser_kwargs: Arguments for ``ArgumentParser.__init__``, optional.
            See more at `Argparse docs`_
    Returns:
        (ArgumentParser): parser with ``--config`` argument

    .. _`Argparse docs`:
        https://docs.python.org/3/library/argparse.html#argumentparser-objects
    """
    argparser_kwargs = argparser_kwargs
    parser_ = argparse.ArgumentParser(**argparser_kwargs)

    parser_.add_argument(
        "-C", "--config", "--configs",
        nargs="+",
        required=True,
        dest="configs",
        help="Path to a config file/files (YAML or JSON)",
        metavar="{PATH}"
    )
    return parser_


class OrderedLoader(yaml.Loader):
    pass


def construct_mapping(loader, node):
    loader.flatten_mapping(node)
    return OrderedDict(loader.construct_pairs(node))


OrderedLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping
)


def load_config(
        path: Union[str, Path],
        ordered: bool = False,
        encoding: str = "utf-8"
) -> Storage:
    warnings.warn(
        "`safitty.load_config` is deprecated, use `safitty.load` instead",
        DeprecationWarning
    )

    return load(path, ordered, encoding)


def load(
        path: Union[str, Path],
        ordered: bool = False,
        encoding: str = "utf-8"
) -> Storage:
    """Loads config by giving path. Supports YAML and JSON files.
    Args:
        path (str): path to config file (YAML or JSON)
        ordered (bool): if true the config will be loaded as ``OrderedDict``
        encoding (str): encoding to read the config
    Returns:
        (Storage): Config
    Raises:
        Exception: if path ``config_path`` doesn't exists or file format is not YAML or JSON
    Examples:
        >>> load(path="./config.yml", ordered=True)
    """
    if isinstance(path, str):
        config_path = Path(path)
    else:
        config_path = path

    if not config_path.exists():
        raise Exception(f"Path '{path}' doesn't exist!")

    config = None
    with config_path.open(encoding=encoding) as stream:
        ext = config_path.suffix

        if ext == ".json":
            object_pairs_hook = OrderedDict if ordered else None
            file = "\n".join(stream.readlines())
            if file != "":
                config = json.loads(file, object_pairs_hook=object_pairs_hook)

        elif ext == ".yml":
            loader = OrderedLoader if ordered else yaml.Loader
            config = yaml.load(stream, loader)
        else:
            raise Exception(f"Unknown file format '{ext}'")

    if config is None:
        return dict()

    return config


def type_from_str(dtype: str) -> Type:
    """Returns type by giving string
    Args:
        dtype (str): string representation of type
    Returns:
        (Type): type
    Examples:
        >>> type_from_str("str")
        str
        >>> type_from_str("int")
        int
        >>> type(type_from_str("int"))
        type
    """
    return locate(dtype)


def parse_content(value: str) -> Any:
    """Parses strings ``value:dtype`` into typed value. If you don't want to parse ``:`` as type
        then wrap input with quotes
    Args:
        value (str): string with form ``value:dtype`` or ``value``
    Returns:
        (Any): value of type ``dtype``, if ``dtype`` wasn't specified value will be parsed as string
    Examples:
        >>> parse_content("True:bool")
        True # type is bool
        >>> parse_content("True:str")
        "True" # type is str
        >>> parse_content("True")
        "True" # type is str
        >>> parse_content("'True:bool'")
        'True:bool' # type is str
        >>> parse_content("some str")
        "some str" # type is str
        >>> parse_content("1:int")
        1 # type is int
        >>> parse_content("1:float")
        1.0 # type is float
        >>> parse_content("[1,2]:list")
        [1, 2] # type is list
        >>> parse_content("'[1,2]:list'")
        '[1,2]:list' # type is str
    """
    quotes_wrap = """^["'][^ ].*[^ ]["']$"""
    if re.match(quotes_wrap, value) is not None:
        value_content = value[1:-1]
        return value_content

    content = value.rsplit(":", 1)
    if len(content) == 1:
        value_content, value_type = content[0], "str"
    else:
        value_content, value_type = content

    result = value_content

    if value_type in ["set", "list", "dict", "frozenset"]:
        try:
            result = eval(f"{value_type}({value_content})")
        except Exception:
            result = value_content
    else:
        value_type = type_from_str(value_type)
        if value_type is not None:
            result = value_type(value_content)

    return result


def update_config_from_args(config: Storage, args: List[str]) -> Storage:
    """Updates configuration file with list of arguments
    Args:
        config (Storage): configuration dict
        args (List[str]): list of arguments with form ``--key:dtype:value:dtype``
    Returns:
        (Storage): updated config
    """
    updated_config = copy.deepcopy(config)

    for argument in args:
        names, value = argument.split("=")
        names = names.lstrip("-").strip("/")

        value = parse_content(value)
        names = [parse_content(name) for name in names.split("/")]

        updated_config = safitty.set(updated_config, *names, value=value)

    return updated_config


def load_config_from_args(
        *,
        parser: Optional[argparse.ArgumentParser] = None,
        arguments: Optional[List[str]] = None,
        ordered: bool = False
) -> (argparse.Namespace, Storage):
    warnings.warn(
        "`safitty.load_config_from_args` is deprecated, use `safitty.load_from_args` instead",
        DeprecationWarning
    )

    return load_from_args(
        parser=parser, arguments=arguments, ordered=ordered
    )


def load_from_args(
        *,
        parser: Optional[argparse.ArgumentParser] = None,
        arguments: Optional[List[str]] = None,
        ordered: bool = False
) -> (argparse.Namespace, Storage):
    """Parses command line arguments, loads config and updates it with unknown args
    Args:
        parser (ArgumentParser, optional): an argument parser
            if none uses ``safitty.argparser()`` by default
        arguments (List[str], optional): arguments to parse, if None uses command line arguments
        ordered (bool): if True loads the config as an ``OrderedDict``
    Returns:
        (Namespace, Storage): arguments from args and a
            config dict with updated values from unknown args
    Examples:
        >>> load_from_args(
        >>>    arguments="-C examples/config.json examples/another.yml --paths/jsons/0:int=uno".split()
        >>> )
    """
    parser = parser or argparser()

    args, uargs = parser.parse_known_args(args=arguments)
    config = {}
    if hasattr(args, "config"):
        config = load_config(args.config, ordered=ordered)

    if hasattr(args, "configs"):
        for i, config_path in enumerate(args.configs):
            config_ = load_config(config_path, ordered=ordered)
            config.update(config_)
    config = update_config_from_args(config, uargs)
    return args, config
