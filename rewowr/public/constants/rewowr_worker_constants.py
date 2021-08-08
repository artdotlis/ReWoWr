# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
import asyncio
from concurrent.futures import thread

from typing import Tuple, Type, final, Final
from dataclasses import dataclass

from rewowr.public.interfaces.container_interface import ContainerInterface
from rewowr.simple_logger.synchronised_standard_output import SyncStdout

ContainerTypes: Final = Tuple[Type[ContainerInterface], ...]
DataContainer: Final = Tuple[Tuple[ContainerInterface, ...], ...]


@final
@dataclass
class WorkerTypeParam:
    cont_in: ContainerTypes
    cont_out: ContainerTypes


@final
@dataclass
class WorkerContainerTypes:
    worker_cont: WorkerTypeParam
    reader_cont: ContainerTypes
    writer_cont: ContainerTypes


@final
@dataclass
class WorkerPref:
    sync_out: SyncStdout
    name_id: str


@final
@dataclass
class PoolLoopCont:
    th_exec: thread.ThreadPoolExecutor
    loop: asyncio.AbstractEventLoop
