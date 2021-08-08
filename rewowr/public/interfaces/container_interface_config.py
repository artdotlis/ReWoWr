# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
from typing import Final

from rewowr.public.container.empty_container import EmptyContainer
from rewowr.public.interfaces.rewrwo_checker_interface import ContainerDict

_LocalContDict: Final[ContainerDict] = ContainerDict(
    container_dict={
        # "ContainerName": ContainerClass
        "EmptyContainer": EmptyContainer
    }
)


def get_rewowr_container_interface_config() -> ContainerDict:
    return _LocalContDict
