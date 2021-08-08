# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
import multiprocessing

import re
from typing import Dict, Tuple, Pattern, final, Final

from rewowr.rewowr_library.rewowr_worker.workable.re_wr_implementation.no_output_sink import \
    NoOutputSink
from rewowr.public.constants.config_constants import ContainerDict
from rewowr.public.interfaces.rewrwo_checker_interface import ExtraArgsReWrWo, ReWrWoDictElem
from rewowr.rewowr_library.rewowr_worker.workable.re_wr_implementation.synchronised_queue import \
    SyncQueue
from rewowr.public.interfaces.re_wr_interface import ReWrInterface
from rewowr.public.errors.custom_errors import WrongExtraArgsPubError
from rewowr.public.functions.check_re_wr_wo_arguments import \
    check_args_sync_queue_similar, check_param_names, check_parse_type
from rewowr.public.functions.check_container import check_container


@final
class _CheckSyncQueue(ReWrWoDictElem[ReWrInterface]):

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
                        cont_dict: ContainerDict, extra_args: ExtraArgsReWrWo, /) -> SyncQueue:
        container_proto, puffer_size = check_args_sync_queue_similar(2, extra_args, cont_dict)
        return SyncQueue(ctx, container_proto, puffer_size)


_COMMA: Final[Pattern[str]] = re.compile(r',')


@final
class _CheckNoOutputSink(ReWrWoDictElem[ReWrInterface]):

    def check_args_func(self, ctx: multiprocessing.context.SpawnContext,
                        cont_dict: ContainerDict, extra_args: ExtraArgsReWrWo, /) \
            -> NoOutputSink:
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
        return NoOutputSink(container_proto)

    def check_numbers(self, worker_in_cnt: int, worker_out_cnt: int,
                      workable_cnt: int, /) -> Tuple[bool, str]:
        if workable_cnt < 1:
            return False, "Workable_cnt can not be smaller than 1!"
        if worker_in_cnt < 0:
            return False, "Worker_in_cnt can not be smaller than 0!"
        if worker_out_cnt < 0:
            return False, "Worker_out_cnt can not be smaller than 0!"
        return True, ""


_LocalReWrDict: Final[Dict[str, ReWrWoDictElem[ReWrInterface]]] = {
    "SyncQueue": _CheckSyncQueue(),
    "NoOutputSink": _CheckNoOutputSink()
}


def get_rewowr_re_wr_interface_config() -> Dict[str, ReWrWoDictElem[ReWrInterface]]:
    return _LocalReWrDict
