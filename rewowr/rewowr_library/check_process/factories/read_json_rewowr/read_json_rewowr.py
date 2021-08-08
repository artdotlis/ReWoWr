# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""
import json
from enum import Enum
from pathlib import Path
from typing import Dict, Type, TypeVar, Final

from rewowr.rewowr_library.check_process.constants.check_constants import ReWoWrStructure, \
    ReWoWrStructureKeys, WorkableConfKeys, WorkerConfKeys, WorkableConf, WorkerConf, \
    NodesReservedNames
from rewowr.rewowr_library.check_process.errors.custom_errors import ReadJsonReWoWrError


def _check_inner_parts(keys_enum: Type[Enum], dict_to_check: Dict, /) -> None:
    for enum_elem in keys_enum:
        if enum_elem.value.index not in dict_to_check:
            raise ReadJsonReWoWrError(f"The key {enum_elem.value.index} is missing!")
        if not isinstance(dict_to_check[enum_elem.value.index], enum_elem.value.type):
            raise ReadJsonReWoWrError(
                f"The {enum_elem.value.index} element is not a {enum_elem.value.type}!"
            )


_ContainerOut: Final = TypeVar("_ContainerOut", WorkerConf, WorkableConf)


def _create_dict_container(structure_type: Type[_ContainerOut],
                           structure_enum: Type[Enum],
                           given_dict: Dict, /) -> Dict[str, _ContainerOut]:
    dict_puf = {}
    for key_dict, dict_value in given_dict.items():
        kwargs_loc = {
            enum_elem.name: dict_value[enum_elem.value.index]
            for enum_elem in structure_enum
        }
        dict_puf[key_dict] = structure_type(**kwargs_loc)

    return dict_puf


def parse_re_wo_wr(json_container: Dict, /) -> ReWoWrStructure:
    _check_inner_parts(ReWoWrStructureKeys, json_container)
    for dict_elem in json_container[ReWoWrStructureKeys.workable_conf.value.index].values():
        _check_inner_parts(WorkableConfKeys, dict_elem)
    for forbidden_enum in NodesReservedNames:
        if forbidden_enum.value in json_container[ReWoWrStructureKeys.worker_conf.value.index]:
            raise ReadJsonReWoWrError(f"WorkerConf can't have {forbidden_enum.value} elements!")

    for dict_elem in json_container[ReWoWrStructureKeys.worker_conf.value.index].values():
        _check_inner_parts(WorkerConfKeys, dict_elem)

    return ReWoWrStructure(
        workable_conf=_create_dict_container(
            WorkableConf,
            WorkableConfKeys,
            json_container[ReWoWrStructureKeys.workable_conf.value.index]
        ),
        worker_conf=_create_dict_container(
            WorkerConf,
            WorkerConfKeys,
            json_container[ReWoWrStructureKeys.worker_conf.value.index]
        )
    )


def read_json_re_wo_wr(json_file: Path, /) -> ReWoWrStructure:
    if not json_file.is_file() or json_file.suffix != '.json':
        raise ReadJsonReWoWrError(
            "The given path is wrong or the file has the wrong format!"
        )
    with json_file.open('r') as fh_1:
        json_container = json.load(fh_1)

    if not isinstance(json_container, dict):
        raise ReadJsonReWoWrError("The the json-root is not a dict!")

    return parse_re_wo_wr(json_container)
