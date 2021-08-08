# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
import multiprocessing

import re
from typing import Dict, Pattern, Tuple, final, Final

from rewowr.rewowr_library.rewowr_worker.workable.wo_implementation.end_work import EndWork
from rewowr.rewowr_library.rewowr_worker.workable.wo_implementation.pass_through import PassThrough
from rewowr.public.interfaces.work_interface import WorkInterface
from rewowr.public.interfaces.rewrwo_checker_interface import ExtraArgsReWrWo, ContainerDict, \
    ReWrWoDictElem
from rewowr.public.errors.custom_errors import WrongExtraArgsPubError
from rewowr.public.functions.check_re_wr_wo_arguments import \
    check_parse_type, check_param_names
from rewowr.public.functions.check_container import check_container


@final
class _CheckEndWork(ReWrWoDictElem[WorkInterface]):

    def check_numbers(self, worker_in_cnt: int, worker_out_cnt: int,
                      workable_cnt: int, /) -> Tuple[bool, str]:
        if workable_cnt < 1:
            return False, "Workable_cnt can not be smaller than 1!"
        if worker_in_cnt > 0:
            return False, "Worker_in_cnt can not be larger than 0!"
        if worker_out_cnt < 0:
            return False, "Worker_out_cnt can not be smaller than 0!"
        return True, ""

    def check_args_func(self, ctx: multiprocessing.context.SpawnContext,
                        cont_dict: ContainerDict, extra_args: ExtraArgsReWrWo, /) -> EndWork:
        return EndWork()


_COMMA: Final[Pattern[str]] = re.compile(r',')


@final
class _CheckPassThrough(ReWrWoDictElem[WorkInterface]):

    def check_numbers(self, worker_in_cnt: int, worker_out_cnt: int,
                      workable_cnt: int, /) -> Tuple[bool, str]:
        if workable_cnt < 1:
            return False, "Workable_cnt can not be smaller than 1!"
        if worker_in_cnt < 0:
            return False, "Worker_in_cnt can not be smaller than 0!"
        if worker_out_cnt < 0:
            return False, "Worker_out_cnt can not be smaller than 0!"
        return True, ""

    def check_args_func(self, ctx: multiprocessing.context.SpawnContext,
                        cont_dict: ContainerDict, extra_args: ExtraArgsReWrWo, /) -> PassThrough:
        param_name = "container_proto"
        check_param_names(extra_args.arguments, [param_name])
        if not isinstance(extra_args.arguments[param_name], str):
            raise WrongExtraArgsPubError(f"Type of {param_name} must be str!")
        container_types_str = tuple(
            check_parse_type(extra_args.arguments[param_name], _COMMA.split)
        )
        container_proto = tuple(
            check_container(cont_type, cont_dict)
            for cont_type in container_types_str
        )
        return PassThrough(container_proto)


_LocalWoDict: Final[Dict[str, ReWrWoDictElem[WorkInterface]]] = {
    "EndWork": _CheckEndWork(),
    "PassThrough": _CheckPassThrough()
}


def get_rewowr_work_interface_config() -> Dict[str, ReWrWoDictElem[WorkInterface]]:
    return _LocalWoDict
