# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
from enum import Enum
from typing import Dict, List, Callable, final, Final
from dataclasses import dataclass

from rewowr.rewowr_library.check_process.constants.check_constants import ReWoWrStructure, \
    NodesReservedNames, WorkerConf, WorkableWCheck
from rewowr.rewowr_library.check_process.errors.custom_errors import CheckWorkerError
from rewowr.public.constants.rewowr_worker_constants import ContainerTypes
from rewowr.public.interfaces.rewrwo_checker_interface import ContainerDict
from rewowr.public.functions.check_container import check_container


@final
@dataclass
class WorkerNode:
    visited: int
    visited_list: List[str]
    in_nodes: List[str]
    out_nodes: List[str]
    in_wa: str
    out_wa: str


@final
@dataclass
class _StartNode:
    reversed_end_cnt: int
    nodes: List[str]


@final
@dataclass
class _EndNode:
    end_cnt: int
    nodes: List[str]


@final
@dataclass
class EndStartNodes:
    start_nodes: Dict[str, _StartNode]
    end_nodes: Dict[str, _EndNode]


@final
@dataclass
class _CheckedWorker:
    worker_structure_chain: Dict[str, WorkerNode]
    start_end_structure: EndStartNodes
    new_used_workable_dict: Dict[str, int]
    new_container_in_dict: Dict[str, ContainerTypes]
    new_container_out_dict: Dict[str, ContainerTypes]


def _compare_int_to_limit(value: int, limit: int, err_msg: str, /) -> None:
    if value <= limit:
        raise CheckWorkerError(err_msg)


def _create_add_new_used_workable_dict(workable_new: str, group_cnt: int,
                                       workable_dict: Dict[str, List[WorkableWCheck]],
                                       new_used_workable_dict: Dict[str, int], /) -> None:
    if workable_new not in workable_dict:
        raise CheckWorkerError(f"Missing {workable_new} in workable_dict!")

    if new_used_workable_dict.setdefault(workable_new, group_cnt) < group_cnt:
        new_used_workable_dict[workable_new] = group_cnt


def _add_worker_to_worker_structure_chain(worker_structure_chain: Dict[str, WorkerNode],
                                          start_end_structure: EndStartNodes,
                                          worker_id: str, worker: WorkerConf, /) -> None:
    if NodesReservedNames.start_node.value in worker.worker_in:
        if worker.workable_in not in start_end_structure.start_nodes:
            start_end_structure.start_nodes[worker.workable_in] = _StartNode(
                nodes=[], reversed_end_cnt=0
            )

        start_end_structure.start_nodes[worker.workable_in].nodes.append(worker_id)

    if NodesReservedNames.end_node.value in worker.worker_out:
        if worker.workable_out not in start_end_structure.end_nodes:
            start_end_structure.end_nodes[worker.workable_out] = _EndNode(nodes=[], end_cnt=0)

        start_end_structure.end_nodes[worker.workable_out].nodes.append(worker_id)

    worker_structure_chain[worker_id] = WorkerNode(
        visited=0, visited_list=[],
        in_nodes=[node for node in worker.worker_in if node != NodesReservedNames.start_node.value],
        out_nodes=[node for node in worker.worker_out if node != NodesReservedNames.end_node.value],
        in_wa=worker.workable_in,
        out_wa=worker.workable_out
    )


def _check_worker_in_out(worker_in_out: List[str], worker_conf: Dict[str, WorkerConf],
                         exclude_id: str, include_start_stop_id: str, /) -> None:
    if (
            not worker_in_out
            or len(set(worker_in_out)) != len(worker_in_out)
            or exclude_id in worker_in_out
    ):
        raise CheckWorkerError(f"The worker_in_out param: {worker_in_out} is wrong!")

    if include_start_stop_id in worker_in_out and len(worker_in_out) != 1:
        raise CheckWorkerError(
            f"The {worker_in_out} list with the {include_start_stop_id}"
            + " element can't have other elements!"
        )

    for worker_in_index in worker_in_out:
        if (
                include_start_stop_id != worker_in_index
                and not (isinstance(worker_in_index, str) and worker_in_index in worker_conf)
        ):
            raise CheckWorkerError(f"The worker_in_out id: {worker_in_index} is missing!")


@final
@dataclass
class _WorkablePuf:
    worker_in: List[str]
    worker_out: List[str]


@final
class _WorkerConnection(Enum):
    worker_in = 1
    worker_out = 2


def _get_nodes_out(node: WorkerNode, _: str, /) -> List[str]:
    return node.out_nodes


def _get_nodes_in(node: WorkerNode, _: str, /) -> List[str]:
    return node.in_nodes


def _get_error(_: WorkerNode, error_msg: str, /) -> List[str]:
    raise CheckWorkerError(error_msg)


_SwitchConnection: Final[Dict[_WorkerConnection, Callable[[WorkerNode, str], List[str]]]] = {
    _WorkerConnection.worker_in: _get_nodes_out,
    _WorkerConnection.worker_out: _get_nodes_in
}


def _compare_worker_connectivity(workable_for: List[str], workable_comp: List[str],
                                 worker_enum: _WorkerConnection,
                                 worker_structure_chain: Dict[str, WorkerNode], /) -> None:
    for worker_elem_id in workable_for:
        worker_elem_nodes = _SwitchConnection.get(worker_enum, _get_error)(
            worker_structure_chain[worker_elem_id], "Wrong worker enum!"
        )
        if len(worker_elem_nodes) != len(workable_comp):
            raise CheckWorkerError(
                f"The worker {worker_elem_id} expected to connect to {worker_elem_nodes}"
                + f" but the workable has the following connections {workable_comp}"
            )
        for connect_id in worker_elem_nodes:
            if connect_id not in workable_comp:
                raise CheckWorkerError(
                    f"The worker {worker_elem_id} is missing the connection {connect_id}!"
                )


def _check_container_types(workable_dict: Dict[str, _WorkablePuf],
                           conatiner_in: Dict[str, ContainerTypes],
                           container_out: Dict[str, ContainerTypes], /) -> None:
    for workable_id, workable in workable_dict.items():
        container_in_list = [
            container_class
            for worker_id in workable.worker_in
            for container_class in conatiner_in[worker_id]
        ]
        if len(container_in_list) != len(set(container_in_list)):
            raise CheckWorkerError(f"Workable {workable_id} has overlapping container in tuple!")
        container_out_list = [
            container_class
            for worker_id in workable.worker_out
            for container_class in container_out[worker_id]
        ]
        if len(container_out_list) != len(set(container_out_list)):
            raise CheckWorkerError(f"Workable {workable_id} has overlapping container out tuple!")

        if container_out_list and container_in_list:
            if len(container_out_list) != len(container_in_list):
                raise CheckWorkerError(
                    f"Mismatched container_in ({len(container_in_list)})"
                    + f" and container_out ({len(container_out_list)}) length!"
                )
            for container_out_elem in container_out_list:
                if container_out_elem not in container_in_list:
                    raise CheckWorkerError(f"Missing container_out {container_out_elem.__name__}")

        if not (container_out_list or container_in_list):
            raise CheckWorkerError(f"Workable {workable_id} is empty!")


def _check_worker_to_worker_structure_chain(checked_worker: _CheckedWorker, /) -> None:
    worker_structure_chain: Dict[str, WorkerNode] = checked_worker.worker_structure_chain
    puf_workable: Dict[str, _WorkablePuf] = {}
    for worker_id, worker_elem in worker_structure_chain.items():
        puf_workable.setdefault(
            worker_elem.out_wa, _WorkablePuf([], [])
        ).worker_out.append(worker_id)
        puf_workable.setdefault(
            worker_elem.in_wa, _WorkablePuf([], [])
        ).worker_in.append(worker_id)

    for workable_id, workable_elem in puf_workable.items():
        if len(set(workable_elem.worker_out)) != len(workable_elem.worker_out) or \
                len(set(workable_elem.worker_in)) != len(workable_elem.worker_in):
            raise CheckWorkerError(
                f"The worker_in_out ids on workable: {workable_id} have duplicates!"
            )
        _compare_worker_connectivity(
            workable_elem.worker_out, workable_elem.worker_in,
            _WorkerConnection.worker_in, worker_structure_chain
        )
        _compare_worker_connectivity(
            workable_elem.worker_in, workable_elem.worker_out,
            _WorkerConnection.worker_out, worker_structure_chain
        )

    _check_container_types(
        puf_workable, checked_worker.new_container_in_dict, checked_worker.new_container_out_dict
    )


def check_worker(re_wr_wo_structure: ReWoWrStructure,
                 workable_dict: Dict[str, List[WorkableWCheck]],
                 container_dict: ContainerDict, /) -> _CheckedWorker:
    output = _CheckedWorker(
        worker_structure_chain={},
        start_end_structure=EndStartNodes(start_nodes={}, end_nodes={}),
        new_used_workable_dict={},
        new_container_in_dict={},
        new_container_out_dict={}
    )

    for worker_index, worker_elem in re_wr_wo_structure.worker_conf.items():
        _compare_int_to_limit(
            worker_elem.group_cnt, 0,
            f"Worker {worker_index} have {worker_elem.group_cnt} as group_cnt!"
        )
        _compare_int_to_limit(
            worker_elem.process_cnt, 0,
            f"Worker {worker_index} have {worker_elem.process_cnt} as process_cnt!"
        )

        _create_add_new_used_workable_dict(
            worker_elem.workable_in, worker_elem.group_cnt,
            workable_dict, output.new_used_workable_dict,
        )
        _create_add_new_used_workable_dict(
            worker_elem.workable_out, worker_elem.group_cnt,
            workable_dict, output.new_used_workable_dict,
        )

        _check_worker_in_out(
            worker_elem.worker_in, re_wr_wo_structure.worker_conf,
            NodesReservedNames.end_node.value, NodesReservedNames.start_node.value
        )
        _check_worker_in_out(
            worker_elem.worker_out, re_wr_wo_structure.worker_conf,
            NodesReservedNames.start_node.value, NodesReservedNames.end_node.value
        )

        _add_worker_to_worker_structure_chain(
            output.worker_structure_chain, output.start_end_structure,
            worker_index, worker_elem
        )

        output.new_container_in_dict[worker_index] = tuple(
            check_container(cont, container_dict)
            for cont in worker_elem.work_type_in if isinstance(cont, str)
        )
        output.new_container_out_dict[worker_index] = tuple(
            check_container(cont, container_dict)
            for cont in worker_elem.work_type_out if isinstance(cont, str)
        )

    _check_worker_to_worker_structure_chain(output)

    return output
