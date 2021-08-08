# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
import multiprocessing
import abc
from typing import Dict, Type, TypeVar, Generic, Tuple, final, Final

from dataclasses import dataclass

from rewowr.public.interfaces.container_interface import ContainerInterface
from rewowr.public.interfaces.re_wr_interface import ReWrInterface
from rewowr.public.interfaces.work_interface import WorkInterface


@final
@dataclass
class ExtraArgsReWrWo:
    arguments: Dict[str, str]


@final
@dataclass
class ContainerDict:
    container_dict: Dict[str, Type[ContainerInterface]]


_ReWrWoDictElemType: Final = TypeVar('_ReWrWoDictElemType', ReWrInterface, WorkInterface)


class ReWrWoDictElem(Generic[_ReWrWoDictElemType], abc.ABC):
    @abc.abstractmethod
    def check_args_func(self, ctx: multiprocessing.context.SpawnContext,
                        cont_dict: ContainerDict, extra_args: ExtraArgsReWrWo, /) \
            -> _ReWrWoDictElemType:
        raise NotImplementedError("Interface!")

    @abc.abstractmethod
    def check_numbers(self, worker_in_cnt: int, worker_out_cnt: int, workable_cnt: int, /) \
            -> Tuple[bool, str]:
        """ TODO doc not finished
            True = No Error
            False = Error
           Notice: worker_in_cnt and  worker_out_cnt can be zero
            and thus should not be tested (no connections). This should not raise any Errors!
            workable_cnt can not be zero!
        """
        raise NotImplementedError("Interface!")
