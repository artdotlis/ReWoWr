# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
import asyncio
from typing import List, final

from rewowr.rewowr_library.rewowr_worker.workable.workable_elem import Workable


@final
class WorkableManager:

    def __init__(self, workable_in: List[Workable], workable_out: List[Workable], /) -> None:
        super().__init__()
        self.__read_from: List[Workable] = workable_in
        self.__write_to: List[Workable] = workable_out

    @property
    def workable_in(self) -> List[Workable]:
        return self.__read_from

    @property
    def workable_out(self) -> List[Workable]:
        return self.__write_to

    def set_error_in_workables(self) -> None:
        for pr_workable in self.__read_from:
            pr_workable.workable_set_error()
        for re_workable in self.__write_to:
            re_workable.workable_set_error()

    def provider_process_started(self) -> None:
        for re_workable in self.__write_to:
            re_workable.workable_add_provider()

    def provider_process_stopped(self) -> None:
        for write_to in self.__write_to:
            write_to.workable_remove_provider()
            write_to.workable_shutdown()
        for read_from in self.__read_from:
            read_from.workable_on_close()
            read_from.workable_shutdown()

    def init_all_workables(self, loop: asyncio.AbstractEventLoop, /) -> None:
        for pr_workable in self.__read_from:
            pr_workable.login_loop_th_pool(loop)
        for re_workable in self.__write_to:
            re_workable.login_loop_th_pool(loop)

    def check_block(self) -> None:
        # block until all workables from reader are finished
        block = True
        while block:
            block = False
            for workable in self.__read_from:
                if workable.workable_check_block():
                    block = True
