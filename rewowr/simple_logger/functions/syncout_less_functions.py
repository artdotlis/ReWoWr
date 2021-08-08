# -*- coding: utf-8 -*-
""".. moduleauthor:: Artur Lissin"""

import datetime
from typing import List

from rewowr.simple_logger.constants.synchronised_standard_output_const import \
    get_not_space_pattern, get_time_format_pattern, get_new_line_pattern


def format_message_time(message: str, /) -> List[str]:
    time_form = get_time_format_pattern().search(str(datetime.datetime.now()))
    if time_form is None:
        time_form_str = "unknown"
    else:
        time_form_str = time_form.group(1)

    checked_format = [
        line[:1000]
        for line in get_new_line_pattern().split(message)
        if get_not_space_pattern().search(line) is not None
    ]
    if checked_format:
        formatted_mes = [
            " {0} | {1}".format(time_form_str, checked_format[0])
        ]
        if len(checked_format) > 1:
            buffer = "".join(" " for _ in range(len(time_form_str)))
            formatted_mes = formatted_mes + [
                " {0} | {1}".format(buffer, line) for line in checked_format[1:]
            ]

        return formatted_mes

    return []
