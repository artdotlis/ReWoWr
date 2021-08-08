# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple, final

from rewowr.rewowr_library.check_process.errors.custom_errors import CheckWorkerPathError
from rewowr.rewowr_library.check_process.check_functions.check_worker import WorkerNode, \
    EndStartNodes


@final
class _NextNodes(Enum):
    nodes_in = 1
    nodes_out = 2


@final
@dataclass
class _StartWorkerNode:
    next_worker_id: str
    workable: str
    path_chain: Tuple[str, ...]


def _rec_walk(worker_con: _StartWorkerNode, worker_structure_chain: Dict[str, WorkerNode],
              start_end_structure: EndStartNodes, node_pos: _NextNodes, /) -> None:
    mom_node = worker_structure_chain[worker_con.next_worker_id]
    if worker_con.next_worker_id in worker_con.path_chain:
        raise CheckWorkerPathError(
            f"A node {worker_con.next_worker_id} in worker path has been visited already!"
        )
    if not (worker_con.path_chain and worker_con.path_chain[-1] in mom_node.visited_list):
        mom_node.visited += 1
        if worker_con.path_chain:
            mom_node.visited_list.append(worker_con.path_chain[-1])
    if worker_con.workable != _get_next_wa(mom_node, node_pos)[0]:
        raise CheckWorkerPathError(
            "A connection {0} in worker path has different types: {1} {2}!".format(
                worker_con.next_worker_id, _get_next_wa(mom_node, node_pos)[0],
                worker_con.workable
            )
        )
    for next_node in _get_next_nodes(mom_node, node_pos)[1]:
        _rec_walk(
            _StartWorkerNode(
                next_node, _get_next_wa(mom_node, node_pos)[1],
                (*worker_con.path_chain, worker_con.next_worker_id)
            ),
            worker_structure_chain, start_end_structure, node_pos
        )
    if not _get_next_nodes(mom_node, node_pos)[1]:
        to_add_l = False
        if not worker_con.path_chain or len(worker_con.path_chain) == 1:
            to_add_l = True
        elif worker_con.path_chain[0] not in mom_node.visited_list:
            mom_node.visited_list.append(worker_con.path_chain[0])
            to_add_l = True
        if to_add_l:
            _increase_start_end_cnt(
                start_end_structure, _get_next_wa(mom_node, node_pos)[1],
                node_pos
            )


def _increase_start_end_cnt(start_end_structure: EndStartNodes,
                            wa_id: str, node_pos: _NextNodes, /) -> None:
    if _NextNodes.nodes_in == node_pos:
        start_end_structure.end_nodes[wa_id].end_cnt += 1
    if _NextNodes.nodes_out == node_pos:
        start_end_structure.start_nodes[wa_id].reversed_end_cnt += 1


def _get_next_nodes(work_node: WorkerNode,
                    node_pos: _NextNodes, /) -> Tuple[List[str], List[str]]:
    if _NextNodes.nodes_in == node_pos:
        return work_node.in_nodes, work_node.out_nodes
    if _NextNodes.nodes_out == node_pos:
        return work_node.out_nodes, work_node.in_nodes

    raise Exception("Function _get_next_nodes has missing _NextNodes possibilities!")


def _get_next_wa(work_node: WorkerNode,
                 node_pos: _NextNodes, /) -> Tuple[str, str]:
    if _NextNodes.nodes_in == node_pos:
        return work_node.in_wa, work_node.out_wa
    if _NextNodes.nodes_out == node_pos:
        return work_node.out_wa, work_node.in_wa

    raise Exception("Function _get_next_wa has missing _NextNodes possibilities!")


def _check_if_visited(worker_structure_chain: Dict[str, WorkerNode],
                      node_pos: _NextNodes, /) -> None:
    for worker_id, worker_value in worker_structure_chain.items():
        vis_number = len(_get_next_nodes(worker_value, node_pos)[0])
        vis_number = vis_number if vis_number else 1
        if worker_value.visited != vis_number:
            raise CheckWorkerPathError(
                f"The worker {worker_id} has no connections to a start or end node!"
            )
        worker_value.visited = 0
        worker_value.visited_list = []


def check_worker_path(worker_structure_chain: Dict[str, WorkerNode],
                      start_end_structure: EndStartNodes, /) -> None:
    if not start_end_structure.start_nodes:
        raise CheckWorkerPathError("StartNodes are empty!")
    if not start_end_structure.end_nodes:
        raise CheckWorkerPathError("EndNodes are empty!")

    for started_workable, started_nodes in start_end_structure.start_nodes.items():
        for node in started_nodes.nodes:
            _rec_walk(
                _StartWorkerNode(node, started_workable, tuple()),
                worker_structure_chain, start_end_structure, _NextNodes.nodes_in
            )

    _check_if_visited(worker_structure_chain, _NextNodes.nodes_in)

    for end_workable, end_nodes in start_end_structure.end_nodes.items():
        if end_nodes.end_cnt != len(end_nodes.nodes):
            raise CheckWorkerPathError(f"The EndNode {end_workable} was never reached!")

        for node in end_nodes.nodes:
            _rec_walk(
                _StartWorkerNode(node, end_workable, tuple()),
                worker_structure_chain, start_end_structure, _NextNodes.nodes_out
            )

    _check_if_visited(worker_structure_chain, _NextNodes.nodes_out)

    for started_workable, started_nodes in start_end_structure.start_nodes.items():
        if started_nodes.reversed_end_cnt != len(started_nodes.nodes):
            raise CheckWorkerPathError(f"The StartNode {started_workable} was never reached!")
