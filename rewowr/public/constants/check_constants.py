# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
from pathlib import Path

from typing import Union, Dict, final

from dataclasses import dataclass


@final
@dataclass
class FactoryWorkerArgs:
    conf_file: Union[str, Dict]
    working_dir_log: Path
    step_name: str
