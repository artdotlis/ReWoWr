# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
import multiprocessing

from rewowr.rewowr_library.check_process.factories.factory_re_wo_wr_interface import \
    factory_work_interface, factory_re_wr_interface
from rewowr.rewowr_library.check_process.constants.check_constants import WorkableConf, \
    WorkableWCheck
from rewowr.rewowr_library.rewowr_worker.workable.workable_elem import Workable

from rewowr.simple_logger.synchronised_standard_output import SyncStdout
from rewowr.public.functions.check_extra_args_dict import \
    check_extra_args_dict
from rewowr.public.constants.config_constants import ExtraArgsReWrWo, \
    ReWrWoInterfaceDict
from rewowr.public.interfaces.rewrwo_checker_interface import ContainerDict


def factory_workable(workable_conf: WorkableConf, re_wr_wo_dict: ReWrWoInterfaceDict,
                     container_dict: ContainerDict, sync_out: SyncStdout,
                     ctx: multiprocessing.context.SpawnContext, /) -> WorkableWCheck:
    check_extra_args_dict(workable_conf.args_work)
    check_extra_args_dict(workable_conf.args_re_wr)
    work_obj = factory_work_interface(
        ctx, workable_conf.work_interface, re_wr_wo_dict,
        ExtraArgsReWrWo(arguments=workable_conf.args_work), container_dict
    )
    re_wr_obj = factory_re_wr_interface(
        ctx, workable_conf.re_wr_interface, re_wr_wo_dict,
        ExtraArgsReWrWo(arguments=workable_conf.args_re_wr), container_dict
    )
    return WorkableWCheck(
        workable=Workable(sync_out, ctx, work_obj[0], re_wr_obj[0]),
        checker_re_wr=re_wr_obj[1],
        checker_wo=work_obj[1]
    )
