# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
import multiprocessing

from typing import Tuple

from rewowr.public.interfaces.re_wr_interface_config import \
    get_rewowr_re_wr_interface_config
from rewowr.public.interfaces.work_interface_config import \
    get_rewowr_work_interface_config
from rewowr.public.constants.config_constants import ReWrWoInterfaceDict
from rewowr.public.interfaces.rewrwo_checker_interface import ExtraArgsReWrWo, ContainerDict, \
    ReWrWoDictElem
from rewowr.public.interfaces.re_wr_interface import ReWrInterface
from rewowr.public.interfaces.work_interface import WorkInterface
from rewowr.rewowr_library.check_process.errors.custom_errors import CheckArgumentsError


def factory_work_interface(ctx: multiprocessing.context.SpawnContext, work_interface: str,
                           re_wr_wo_dict: ReWrWoInterfaceDict, extra_args: ExtraArgsReWrWo,
                           container_dict: ContainerDict, /) -> \
        Tuple[WorkInterface, ReWrWoDictElem[WorkInterface]]:
    local_work_dict = get_rewowr_work_interface_config()
    if work_interface in local_work_dict:
        if work_interface in re_wr_wo_dict.work_dict:
            raise CheckArgumentsError(f"WorkInterface {work_interface} is not unique!")
        return (
            local_work_dict[work_interface].check_args_func(ctx, container_dict, extra_args),
            local_work_dict[work_interface]
        )
    if work_interface in re_wr_wo_dict.work_dict:
        return (
            re_wr_wo_dict.work_dict[work_interface].check_args_func(
                ctx, container_dict, extra_args
            ),
            re_wr_wo_dict.work_dict[work_interface]
        )
    raise CheckArgumentsError(f"WorkInterface {work_interface} could not be found!")


def factory_re_wr_interface(ctx: multiprocessing.context.SpawnContext, re_wr_interface: str,
                            re_wr_wo_dict: ReWrWoInterfaceDict, extra_args: ExtraArgsReWrWo,
                            container_dict: ContainerDict, /) -> \
        Tuple[ReWrInterface, ReWrWoDictElem[ReWrInterface]]:
    local_re_wr_dict = get_rewowr_re_wr_interface_config()
    if re_wr_interface in local_re_wr_dict:
        if re_wr_interface in re_wr_wo_dict.re_wr_dict:
            raise CheckArgumentsError(f"ReWrInterface {re_wr_interface} is not unique!!")
        return (
            local_re_wr_dict[re_wr_interface].check_args_func(ctx, container_dict, extra_args),
            local_re_wr_dict[re_wr_interface]
        )
    if re_wr_interface in re_wr_wo_dict.re_wr_dict:
        return (
            re_wr_wo_dict.re_wr_dict[re_wr_interface].check_args_func(
                ctx, container_dict, extra_args
            ),
            re_wr_wo_dict.re_wr_dict[re_wr_interface]
        )
    raise CheckArgumentsError(f"ReWrInterface {re_wr_interface} could not be found!")
