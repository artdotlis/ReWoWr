# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
from typing import Type

from rewowr.public.interfaces.rewrwo_checker_interface import ContainerDict
from rewowr.public.interfaces.container_interface_config import \
    get_rewowr_container_interface_config
from rewowr.public.interfaces.container_interface import ContainerInterface
from rewowr.public.container.container_no_connection import NoConnectionContainer
from rewowr.public.errors.custom_errors import WrongContainerError


def check_container(container: str, given_dict: ContainerDict, /) \
        -> Type[ContainerInterface]:
    cont_found = given_dict.container_dict
    if container in get_rewowr_container_interface_config().container_dict:
        if container in given_dict.container_dict:
            raise WrongContainerError(f"Container: {container} is not unique!")
        cont_found = get_rewowr_container_interface_config().container_dict
    elif container not in given_dict.container_dict:
        raise WrongContainerError(f"Container: {container} could not be found!")

    if (
            cont_found[container] == ContainerInterface
            or cont_found[container] == NoConnectionContainer
            or not issubclass(cont_found[container], ContainerInterface)
    ):
        raise WrongContainerError(
            f"Container: {container} is abstract or not subclass of ContainerInterface!"
        )
    return cont_found[container]
