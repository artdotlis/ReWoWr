# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""

from enum import Enum
from typing import Dict, Type, final
from dataclasses import dataclass

from rewowr.rewowr_library.rewowr_worker.workable.workable_elem import Workable
from rewowr.public.interfaces.rewrwo_checker_interface import ReWrWoDictElem
from rewowr.public.interfaces.re_wr_interface import ReWrInterface
from rewowr.public.interfaces.work_interface import WorkInterface


@final
@dataclass
class WorkableConf:
    re_wr_interface: str
    work_interface: str
    args_re_wr: Dict[str, str]
    args_work: Dict[str, str]


@final
@dataclass
class _EnumIndexType:
    index: str
    type: Type


@final
class WorkableConfKeys(Enum):
    re_wr_interface = _EnumIndexType("ReWrInterface", str)
    work_interface = _EnumIndexType("WorkInterface", str)
    args_re_wr = _EnumIndexType("ArgsReWr", dict)
    args_work = _EnumIndexType("ArgsWork", dict)


@final
@dataclass
class WorkerConf:
    process_cnt: int
    group_cnt: int
    workable_in: str
    workable_out: str
    worker_in: list
    worker_out: list
    work_type_in: list
    work_type_out: list


@final
class WorkerConfKeys(Enum):
    process_cnt = _EnumIndexType("ProcessCnt", int)
    group_cnt = _EnumIndexType("GroupCnt", int)
    workable_in = _EnumIndexType("WorkableIn", str)
    workable_out = _EnumIndexType("WorkableOut", str)
    worker_in = _EnumIndexType("WorkerIn", list)
    worker_out = _EnumIndexType("WorkerOut", list)
    work_type_in = _EnumIndexType("WorkInTypes", list)
    work_type_out = _EnumIndexType("WorkOutTypes", list)


@final
@dataclass
class ReWoWrStructure:
    workable_conf: Dict[str, WorkableConf]
    worker_conf: Dict[str, WorkerConf]


@final
class ReWoWrStructureKeys(Enum):
    workable_conf = _EnumIndexType("WorkableConf", dict)
    worker_conf = _EnumIndexType("WorkerConf", dict)


@final
class NodesReservedNames(Enum):
    start_node = "Start"
    end_node = "End"


@final
@dataclass
class WorkableWCheck:
    workable: Workable
    checker_re_wr: ReWrWoDictElem[ReWrInterface]
    checker_wo: ReWrWoDictElem[WorkInterface]
