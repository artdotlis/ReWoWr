# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""

from enum import Enum
from typing import Dict, List, Tuple, Callable, Union, final
from dataclasses import dataclass

from rewowr.rewowr_library.check_process.constants.check_constants import WorkerConf, WorkableWCheck
from rewowr.rewowr_library.check_process.check_functions.check_worker import WorkerNode
from rewowr.rewowr_library.check_process.errors.custom_errors import CheckWorkableNumbersError


@final
@dataclass
class _WorkableInOut:
    in_cnt: Dict[str, int]
    out_cnt: Dict[str, int]


@final
class _WorkableInOutEnum(Enum):
    in_id = 1
    out_id = 2


def _add_to_dict(in_out: _WorkableInOutEnum, dict_to_add: Dict[str, int],
                 worker_conf: Dict[str, WorkerConf], /) -> Callable[[Tuple[str, WorkerNode]], None]:
    def _error(*_: Union[str, WorkerNode]) -> None:
        raise CheckWorkableNumbersError(f"Fatal error occurred: No enum {in_out} found!")

    def _add_to_in(dict_elem_0: str, dict_elem_1: WorkerNode) -> None:
        dict_to_add[dict_elem_1.in_wa] = \
            dict_to_add[dict_elem_1.in_wa] + worker_conf[dict_elem_0].process_cnt

    def _add_to_out(dict_elem_0: str, dict_elem_1: WorkerNode) -> None:
        dict_to_add[dict_elem_1.out_wa] = \
            dict_to_add[dict_elem_1.out_wa] + worker_conf[dict_elem_0].process_cnt

    switch: Dict[_WorkableInOutEnum, Callable[[str, WorkerNode], None]] = {
        _WorkableInOutEnum.in_id: _add_to_in,
        _WorkableInOutEnum.out_id: _add_to_out
    }

    def _add(dict_elem: Tuple[str, WorkerNode]) -> None:
        switch.get(in_out, _error)(dict_elem[0], dict_elem[1])

    return _add


def check_workable_numbers(workable_dict: Dict[str, List[WorkableWCheck]],
                           worker_conf: Dict[str, WorkerConf], workable_number: Dict[str, int],
                           worker_structure: Dict[str, WorkerNode], /) -> None:
    in_cnt_dict: Dict[str, int] = {
        workable_id: 0
        for workable_id in workable_dict.keys()
    }

    out_cnt_dict: Dict[str, int] = {
        workable_id: 0
        for workable_id in workable_dict.keys()
    }
    tuple_list: List[Tuple[str, WorkerNode]] = list(
        (key, value) for key, value in worker_structure.items()
    )
    func_in = _add_to_dict(_WorkableInOutEnum.in_id, in_cnt_dict, worker_conf)
    func_out = _add_to_dict(_WorkableInOutEnum.out_id, out_cnt_dict, worker_conf)
    for list_elem in tuple_list:
        func_in(list_elem)
        func_out(list_elem)

    for workable_id, workable_cnt in workable_number.items():
        erg_re_wr = workable_dict[workable_id][0].checker_re_wr.check_numbers(
            in_cnt_dict[workable_id],
            out_cnt_dict[workable_id],
            workable_cnt
        )
        if not erg_re_wr[0]:
            raise CheckWorkableNumbersError(f"Error in {workable_id}: {erg_re_wr[1]}")

        erg_wo = workable_dict[workable_id][0].checker_wo.check_numbers(
            in_cnt_dict[workable_id],
            out_cnt_dict[workable_id],
            workable_cnt
        )
        if not erg_wo[0]:
            raise CheckWorkableNumbersError(f"Error in {workable_id}: {erg_wo[1]}")
