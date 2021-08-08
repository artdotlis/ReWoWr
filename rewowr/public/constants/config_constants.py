# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
import multiprocessing

from typing import Dict, Type, TypeVar, Tuple, final, Final
from dataclasses import dataclass

from rewowr.public.interfaces.rewrwo_checker_interface import ExtraArgsReWrWo, ContainerDict, \
    ReWrWoDictElem
from rewowr.public.interfaces.re_wr_interface import ReWrInterface
from rewowr.public.interfaces.work_interface import WorkInterface

_ReWrWoClass: Final = TypeVar('_ReWrWoClass', ReWrInterface, WorkInterface)


@final
class _NoCheckNeeded(ReWrWoDictElem[_ReWrWoClass]):

    def __init__(self, class_type: Type[_ReWrWoClass], workable_limit: int,
                 worker_in_limit: int, worker_out_limit: int, /) -> None:
        super().__init__()
        self.__class_type: Type[_ReWrWoClass] = class_type
        self.__workable_limit = workable_limit
        self.__worker_in_limit = worker_in_limit
        self.__worker_out_limit = worker_out_limit

    def check_numbers(self, worker_in_cnt: int, worker_out_cnt: int,
                      workable_cnt: int, /) -> Tuple[bool, str]:
        if workable_cnt < self.__workable_limit:
            return False, f"Workable_cnt can not be smaller than {self.__workable_limit}!"
        if worker_in_cnt < self.__worker_in_limit:
            return False, f"Worker_in_cnt can not be smaller than {self.__worker_in_limit}!"
        if worker_out_cnt < self.__worker_out_limit:
            return False, f"Worker_out_cnt can not be smaller than {self.__worker_out_limit}!"
        return True, ""

    def check_args_func(self, ctx: multiprocessing.context.SpawnContext,
                        cont_dict: ContainerDict, extra_args: ExtraArgsReWrWo, /) -> _ReWrWoClass:
        return self.__class_type()


def no_check_need_no_params(class_type: Type[_ReWrWoClass],
                            workable_limit: int, worker_in_limit: int,
                            worker_out_limit: int, /) -> ReWrWoDictElem[_ReWrWoClass]:
    return _NoCheckNeeded[_ReWrWoClass](
        class_type, workable_limit, worker_in_limit, worker_out_limit
    )


@final
@dataclass
class ReWrWoInterfaceDict:
    work_dict: Dict[str, ReWrWoDictElem[WorkInterface]]
    re_wr_dict: Dict[str, ReWrWoDictElem[ReWrInterface]]
