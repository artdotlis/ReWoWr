# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
from typing import List

from rewowr.rewowr_library.check_process.errors.custom_errors import CheckConnectionContainerError
from rewowr.rewowr_library.rewowr_worker.workable.workable_elem import Workable
from rewowr.public.interfaces.container_interface import ContainerInterface
from rewowr.public.container.container_no_connection import NoConnectionContainer
from rewowr.public.constants.rewowr_worker_constants import WorkerTypeParam, \
    WorkerContainerTypes, ContainerTypes


def _compare_container(cont_first: ContainerTypes, cont_comp: ContainerTypes,
                       error_msg: str, /) -> ContainerTypes:
    if not cont_first:
        return cont_comp

    if len(cont_first) != len(cont_comp):
        raise CheckConnectionContainerError(error_msg)

    for cont_index, cont_type in enumerate(cont_first):
        if cont_type != cont_comp[cont_index]:
            raise CheckConnectionContainerError(error_msg)

    return cont_comp


def _check_illegal_container_interface(name: str, containers: ContainerTypes, /) -> None:
    if not containers:
        raise CheckConnectionContainerError(f"{name} can't have an empty ContainerType tuple!")

    for cont_type in containers:
        if cont_type in (ContainerInterface, NoConnectionContainer):
            raise CheckConnectionContainerError(
                f"{name} can't have an abstract or not connectable container!"
            )


def _check_occurrence_in_tuple(container_small: ContainerTypes, container_big: ContainerTypes,
                               err_msg: str, /) -> None:
    for cont_type in container_small:
        if cont_type not in container_big:
            raise CheckConnectionContainerError(err_msg)


def check_connection_container(reader_list: List[Workable], writer_list: List[Workable],
                               container_in: ContainerTypes, container_out: ContainerTypes, /) \
        -> WorkerContainerTypes:
    if not (len(container_out) and len(container_in)):
        raise CheckConnectionContainerError(
            "Worker can't have an empty accepted or returned Types-List!"
        )

    if (len(container_out) != len(set(container_out))
            or len(container_in) != len(set(container_in))):
        raise CheckConnectionContainerError(
            "Worker can't have duplicates in accepted or returned Types!"
        )

    read_cont: ContainerTypes = tuple()
    write_cont: ContainerTypes = tuple()
    worker_in_cont: ContainerTypes = tuple()
    worker_out_cont: ContainerTypes = tuple()
    for pr_workable in reader_list:
        connection = pr_workable.workable_re_wr_wo_connections()
        _check_illegal_container_interface("Reader", connection.reader_cont)
        _check_illegal_container_interface("Worker_in", connection.worker_cont.cont_in)
        _check_illegal_container_interface("Worker_out", connection.worker_cont.cont_out)

        read_cont = _compare_container(
            read_cont, connection.reader_cont, "Reader List contains different container types!"
        )
        worker_in_cont = _compare_container(
            worker_in_cont, connection.worker_cont.cont_in,
            "Worker_in List contains different container types!"
        )
        worker_out_cont = _compare_container(
            worker_out_cont, connection.worker_cont.cont_out,
            "Worker_out List contains different container types!"
        )

    for re_workable in writer_list:
        connection = re_workable.workable_re_wr_wo_connections()
        _check_illegal_container_interface("Writer", connection.writer_cont)
        write_cont = _compare_container(
            write_cont, connection.writer_cont,
            "Writer List contains different container types!"
        )

    if not (read_cont and worker_in_cont):
        raise CheckConnectionContainerError("Reader or Worker_in missing WorkerContainerTypes!")
    _check_occurrence_in_tuple(
        worker_in_cont, read_cont,
        "Reader and Worker_in have different or abstract container types!"
    )

    if not (write_cont and worker_out_cont):
        raise CheckConnectionContainerError("Writer or Worker_out missing WorkerContainerTypes!")
    _check_occurrence_in_tuple(
        worker_out_cont, write_cont,
        "Writer and Worker_out have different or abstract container types!"
    )

    if len(set(worker_out_cont)) != len(worker_out_cont):
        raise CheckConnectionContainerError("Duplications in Worker_out found!")

    if len(set(worker_in_cont)) != len(worker_in_cont):
        raise CheckConnectionContainerError("Duplications in Worker_in found!")

    if len(set(write_cont)) != len(write_cont):
        raise CheckConnectionContainerError("Duplications in Writer found!")

    if len(set(read_cont)) != len(read_cont):
        raise CheckConnectionContainerError("Duplications in Worker_out and Writer found!")

    _check_occurrence_in_tuple(
        container_in, worker_in_cont, "The types for the Worker are not provided by the Reader!"
    )
    _check_occurrence_in_tuple(
        container_out, worker_out_cont, "The types for the Writer are not provided by the Worker!"
    )

    return WorkerContainerTypes(
        reader_cont=container_in,
        writer_cont=container_out,
        worker_cont=WorkerTypeParam(
            cont_in=container_in,
            cont_out=container_out
        )
    )
