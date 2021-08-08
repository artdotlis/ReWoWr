# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
import re
from typing import List, TypeVar, Callable, Dict, Pattern, Tuple, Final, Any

from rewowr.public.functions.check_container import check_container
from rewowr.public.constants.rewowr_worker_constants import ContainerTypes
from rewowr.public.interfaces.rewrwo_checker_interface import ExtraArgsReWrWo, ContainerDict
from rewowr.public.errors.custom_errors import WrongExtraArgsPubError


def check_param_names(extra_args: Dict[str, str], parameter_names: List[str], /) -> None:
    for name in parameter_names:
        if name not in extra_args:
            raise WrongExtraArgsPubError(f"Parameter: {name} missing in given extra_args!")


_ParsedType: Final = TypeVar('_ParsedType')


def check_parse_type(value: str, type_parse_fun: Callable[[str], _ParsedType], /) -> _ParsedType:
    try:
        return type_parse_fun(value)
    except (ValueError, TypeError) as type_er:
        raise WrongExtraArgsPubError(f"Argument: {value} could not be parsed!") from type_er


_ArgTypeF: Final = TypeVar('_ArgTypeF')


def parse_all_types(value: _ArgTypeF, type_parse_fun: Callable[[Any], _ParsedType], /) \
        -> _ParsedType:
    try:
        return type_parse_fun(value)
    except (ValueError, TypeError) as type_er:
        raise WrongExtraArgsPubError(f"Argument: {value} could not be parsed!") from type_er


_COMMA: Final[Pattern[str]] = re.compile(r',')


def check_args_sync_queue_similar(int_limit: int, extra_args: ExtraArgsReWrWo,
                                  container_dict: ContainerDict, /) -> Tuple[ContainerTypes, int]:
    names = ['puffer_size', 'container_proto']
    check_param_names(extra_args.arguments, names)
    puffer_size = check_parse_type(extra_args.arguments[names[0]], int)
    if puffer_size < int_limit:
        raise WrongExtraArgsPubError(
            "SyncQueue must have at least two elements for workable to work!"
        )
    if not isinstance(extra_args.arguments[names[1]], str):
        raise WrongExtraArgsPubError(f"Type of {names[1]} must be str!")
    container_types_str = tuple(check_parse_type(extra_args.arguments[names[1]], _COMMA.split))
    container_proto = tuple(
        check_container(cont_type, container_dict)
        for cont_type in container_types_str
    )
    return container_proto, puffer_size
