"""
These functions are originally located at `Catalyst. Reproducible and fast DL & RL`_

Some methods were formatted and simplified.

.. _`Catalyst. Reproducible and fast DL & RL`:
    https://github.com/catalyst-team/catalyst
"""
import argparse
import re
import copy

from pathlib import Path
import json
import yaml

from typing import List, Any, Type, Optional
from collections import OrderedDict
from pydoc import locate

from .core import safe_set
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
        "-C", "--config",
        type=str,
        required=True,
        help="Path to a config file (YAML or JSON)",
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


def load_config(path: str, ordered: bool = False) -> Storage:
    """Loads config by giving path. Supports YAML and JSON files.
    Args:
        path (str): path to config file (YAML or JSON)
        ordered (bool): decide if the config should be loaded as ``OrderedDict``
    Returns:
        (Storage): Config
    Raises:
        Exception: if path ``config_path`` doesn't exists or file format is not YAML or JSON
    """
    config_path = Path(path)

    if not config_path.exists():
        raise Exception(f"Path '{path}' doesn't exist!")

    config = None
    with config_path.open() as stream:
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

        updated_config = safe_set(updated_config, *names, value=value)

    return updated_config


def load_config_from_args(
        *,
        parser: Optional[argparse.ArgumentParser] = None,
        arguments: Optional[List[str]] = None,
) -> Storage:
    """Parses command line arguments, loads config and updates it with unknown args
    Args:
        parser (ArgumentParser, optional): an argument parser
            if none uses ``safitty.argparser()`` by default
        arguments (List[str], optional): arguments to parse, if None uses command line arguments
    Returns:
        (Storage): config dict with updated values from unknown args
    Examples:
        >>> load_config_from_args(arguments="-C examples/config.json --paths/jsons/0:int=uno".split())
    """
    parser = parser or argparser()

    args, uargs = parser.parse_known_args(args=arguments)
    config = load_config(args.config, ordered=False)
    return update_config_from_args(config, uargs)
