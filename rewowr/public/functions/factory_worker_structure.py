# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
import multiprocessing

import sys
import time

import threading
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Iterable, Union, final
from dataclasses import dataclass

from rewowr.simple_logger.synchronised_standard_output import SyncStdout, LogManager, \
    SyncStdoutArgs
from rewowr.rewowr_library.check_process.check_functions.check_worker_path import check_worker_path
from rewowr.rewowr_library.check_process.constants.check_constants import ReWoWrStructure, \
    NodesReservedNames, WorkableWCheck
from rewowr.rewowr_library.check_process.factories.read_json_rewowr.read_json_rewowr import \
    read_json_re_wo_wr, parse_re_wo_wr
from rewowr.rewowr_library.rewowr_worker.workable.workable_elem import Workable, WorkerInOut
from rewowr.rewowr_library.check_process.factories.factory_workable import factory_workable
from rewowr.rewowr_library.check_process.check_functions.check_worker import check_worker
from rewowr.rewowr_library.rewowr_worker.rewowr_worker import Worker
from rewowr.rewowr_library.check_process.check_functions.check_workable_connections import \
    check_connection_container
from rewowr.rewowr_library.check_process.check_functions.check_workable_numbers import \
    check_workable_numbers
from rewowr.public.functions.error_handling import RedirectSysHandler, SysHandlerCon
from rewowr.public.constants.check_constants import FactoryWorkerArgs
from rewowr.public.constants.config_constants import ReWrWoInterfaceDict
from rewowr.public.interfaces.rewrwo_checker_interface import ContainerDict
from rewowr.public.errors.custom_errors import KnownError
from rewowr.public.functions.syncout_dep_functions import logger_send_error, \
    logger_print_con, RedirectWriteToLogger, RedirectErrorToLogger
from rewowr.public.constants.rewowr_worker_constants import WorkerPref
from rewowr.public.functions.worker_ctx import get_worker_ctx


def _local_check(sync_out_pr: SyncStdout,
                 pr_list: List[multiprocessing.context.SpawnProcess], /) -> Iterable[int]:
    for pr_elem in pr_list:
        if not sync_out_pr.error_occurred():
            pr_elem.join(2)

        if not pr_elem.is_alive():
            yield 1


@final
@dataclass
class _PrLists:
    worker_pr: List[multiprocessing.context.SpawnProcess]
    extra_pr: List[multiprocessing.context.SpawnProcess]


def _await_processes(workable_dict: Dict[str, List[WorkableWCheck]], pr_lists: _PrLists,
                     sync_out_structure: SyncStdout, sync_out_pr: SyncStdout,
                     std_buffer: RedirectSysHandler, /) -> None:
    loop_cnt_canceled = 0
    if not sync_out_structure.error_occurred():
        for pr_elem in pr_lists.worker_pr:
            pr_elem.start()

        to_close = True
        while to_close:
            cnt = sum(_local_check(sync_out_pr, pr_lists.worker_pr))
            if cnt == len(pr_lists.worker_pr):
                to_close = False

            if sync_out_pr.error_occurred():
                loop_cnt_canceled += 1
                time.sleep(1)

            if loop_cnt_canceled >= 300:
                to_close = False

        if loop_cnt_canceled >= 300 and sync_out_pr.error_occurred():
            for pr_elem in pr_lists.worker_pr:
                pr_elem.terminate()
            _workable_on_terminate(workable_dict)
            for pr_elem in pr_lists.extra_pr:
                pr_elem.terminate()

    std_buffer.join_errors()
    if loop_cnt_canceled < 300:
        logs: List[Union[threading.Thread, multiprocessing.context.SpawnProcess]] = [
            _close_logger(sync_out_pr),
            _close_logger(sync_out_structure),
            *pr_lists.extra_pr
        ]
        for log_elem in logs:
            log_elem.join()
    std_buffer.close()
    if loop_cnt_canceled >= 300:
        print(f"\n\n\n{'#' * 10}\nWARNING! WARNING! PROCESSES WERE TERMINATED!\n{'#' * 10}\n\n\n")


def _close_logger(sync_out: SyncStdout, /) -> threading.Thread:
    sync_out.flush_log_stats()
    sync_out.flush_stats()
    thread_logger_cl = threading.Thread(
        target=sync_out.close_logger
    )
    thread_logger_cl.setDaemon(False)
    thread_logger_cl.start()
    return thread_logger_cl


def _workable_on_error(workable_dict: Dict[str, List[WorkableWCheck]], /) -> None:
    for workable_list in workable_dict.values():
        for workable_elem in workable_list:
            workable_elem.workable.workable_set_error()


def _workable_on_terminate(workable_dict: Dict[str, List[WorkableWCheck]], /) -> None:
    for workable_list in workable_dict.values():
        for workable_elem in workable_list:
            workable_elem.workable.terminated_set_error()


@final
@dataclass
class _SyncIdData:
    sync_out_structure: SyncStdout
    sync_out: SyncStdout
    id_name: str


@final
@dataclass
class _ProcessCon:
    log_manager: LogManager
    worker_process_list: List[multiprocessing.context.SpawnProcess]
    workable_dict: Dict[str, List[WorkableWCheck]]
    extra_pr_list: List[multiprocessing.context.SpawnProcess]


def factory_worker(fact_arguments: FactoryWorkerArgs, re_wr_wo_dict: ReWrWoInterfaceDict,
                   container_dict: ContainerDict, /) -> \
        Iterable[Dict[NodesReservedNames, Dict[str, List[Workable]]]]:
    factory_ctx = get_worker_ctx()
    process_container = _ProcessCon(
        log_manager=LogManager(factory_ctx), worker_process_list=[],
        workable_dict={}, extra_pr_list=[]
    )
    fact_arguments.working_dir_log.joinpath(f"l_{datetime.now().strftime('%d_%m_%Y__%H_%M_%S')}")
    sync_id = _SyncIdData(
        sync_out_structure=SyncStdout(
            SyncStdoutArgs(
                step_name="structure_creating_process",
                working_dir=fact_arguments.working_dir_log
            ), factory_ctx, process_container.log_manager, process_container.extra_pr_list
        ),
        sync_out=SyncStdout(
            SyncStdoutArgs(
                step_name=fact_arguments.step_name,
                working_dir=fact_arguments.working_dir_log
            ), factory_ctx,
            process_container.log_manager, process_container.extra_pr_list
        ),
        id_name="factory_worker"
    )
    handlers = RedirectSysHandler(SysHandlerCon(
        sys_handler=RedirectWriteToLogger(sync_id.sync_out_structure),
        sys_error_h=RedirectErrorToLogger(sync_id.sync_out_structure),
        stdout_buffer=sys.__stdout__,
        stderr_buffer=sys.__stderr__
    ))
    handlers.set_sys_handler()
    try:
        logger_print_con(
            sync_id.sync_out_structure,
            sync_id.id_name,
            "Starting to analyse given re_wr_wo configuration!",
            0.0,
            False
        )
        if isinstance(fact_arguments.conf_file, dict):
            re_wr_wo_structure: ReWoWrStructure = parse_re_wo_wr(fact_arguments.conf_file)
        elif isinstance(fact_arguments.conf_file, str):
            re_wr_wo_structure = read_json_re_wo_wr(Path(fact_arguments.conf_file))
        else:
            raise Exception("Something really strange happened!")

        logger_print_con(
            sync_id.sync_out_structure,
            sync_id.id_name,
            "Finished analysing given re_wr_wo configuration!",
            15.0,
            False
        )
        for key, workable_conf_el in re_wr_wo_structure.workable_conf.items():
            process_container.workable_dict[key] = [
                factory_workable(
                    workable_conf_el, re_wr_wo_dict, container_dict, sync_id.sync_out, factory_ctx
                )
            ]

        logger_print_con(
            sync_id.sync_out_structure,
            sync_id.id_name,
            "Created all defined workables!",
            30.0,
            False
        )

        worker_dict = check_worker(
            re_wr_wo_structure, process_container.workable_dict, container_dict
        )

        logger_print_con(
            sync_id.sync_out_structure,
            sync_id.id_name,
            "Checked and created the worker chain!",
            45.0,
            False
        )

        check_worker_path(worker_dict.worker_structure_chain, worker_dict.start_end_structure)
        check_workable_numbers(
            process_container.workable_dict, re_wr_wo_structure.worker_conf,
            worker_dict.new_used_workable_dict, worker_dict.worker_structure_chain
        )

        logger_print_con(
            sync_id.sync_out_structure,
            sync_id.id_name,
            "Checked if all workers are reachable and all numbers in workables are correct!",
            60.0,
            False
        )

        for workable_id, workable_number in worker_dict.new_used_workable_dict.items():
            process_container.workable_dict[workable_id].extend(
                factory_workable(
                    re_wr_wo_structure.workable_conf[workable_id], re_wr_wo_dict,
                    container_dict, sync_id.sync_out, factory_ctx
                )
                for _ in range(
                    0, workable_number - len(process_container.workable_dict[workable_id])
                )
            )

        logger_print_con(
            sync_id.sync_out_structure,
            sync_id.id_name,
            "Fixed the workable object numbers!",
            80.0,
            False
        )

        process_container.worker_process_list = [
            factory_ctx.Process(target=Worker(
                WorkerPref(
                    sync_out=sync_id.sync_out,
                    name_id=worker_id
                ),
                WorkerInOut(
                    workable_in=[
                        elem.workable for elem in process_container.workable_dict[worker_elem.in_wa]
                    ],
                    workable_out=[
                        elem.workable for elem
                        in process_container.workable_dict[worker_elem.out_wa]
                    ]
                ),
                check_connection_container(
                    [elem.workable for elem in process_container.workable_dict[worker_elem.in_wa]],
                    [elem.workable for elem in process_container.workable_dict[worker_elem.out_wa]],
                    worker_dict.new_container_in_dict[worker_id],
                    worker_dict.new_container_out_dict[worker_id]
                )
            ).run, name="Worker-{0}-({1})".format(
                worker_num + mul * len(worker_dict.worker_structure_chain),
                worker_id
            ))
            for worker_num, (worker_id, worker_elem)
            in enumerate(worker_dict.worker_structure_chain.items(), 1)
            for mul in range(0, re_wr_wo_structure.worker_conf[worker_id].process_cnt)
        ]

        yield {
            NodesReservedNames.start_node: {
                start_in_index: [
                    elem_wa.workable for elem_wa in process_container.workable_dict[start_in_index]
                ]
                for start_in_index in worker_dict.start_end_structure.start_nodes.keys()
            },
            NodesReservedNames.end_node: {
                end_out_index: [
                    elem_wa.workable for elem_wa in process_container.workable_dict[end_out_index]
                ]
                for end_out_index in worker_dict.start_end_structure.end_nodes.keys()
            }
        }

    except KnownError as known_error:
        logger_send_error(
            sync_id.sync_out_structure, 'Expected', known_error,
            sync_id.id_name, traceback.format_exc()
        )
        handlers.on_known_errors(str(known_error))
        _workable_on_error(process_container.workable_dict)
    except Exception as error:
        logger_send_error(
            sync_id.sync_out_structure, 'Not expected', error,
            sync_id.id_name, traceback.format_exc()
        )
        _workable_on_error(process_container.workable_dict)
        handlers.on_exception(str(error))
        raise error
    else:
        logger_print_con(
            sync_id.sync_out_structure,
            sync_id.id_name,
            "All Worker creation [done]!",
            100.0,
            True
        )
    finally:
        _await_processes(
            process_container.workable_dict,
            _PrLists(
                worker_pr=process_container.worker_process_list,
                extra_pr=process_container.extra_pr_list
            ),
            sync_id.sync_out_structure, sync_id.sync_out, handlers
        )
