# -*- coding: utf-8 -*-
#
# QAPI error classes
#
# Copyright (c) 2017-2019 Red Hat Inc.
#
# Authors:
#  Markus Armbruster <armbru@redhat.com>
#  Marc-André Lureau <marcandre.lureau@redhat.com>
#
# This work is licensed under the terms of the GNU GPL, version 2.
# See the COPYING file in the top-level directory.

from typing import Optional

from .source import QAPISourceInfo


class QAPIError(Exception):
    """Base class for all exceptions from the QAPI module."""


class QAPISourceError(QAPIError):
    """Error class for all exceptions identifying a source location."""
    def __init__(self,
                 info: QAPISourceInfo,
                 msg: str,
                 col: Optional[int] = None):
        super().__init__()
        self.info = info
        self.msg = msg
        self.col = col

    def __str__(self) -> str:
        loc = str(self.info)
        if self.col is not None:
            loc += f":{self.col}"
        return f"{loc}: {self.msg}"


class QAPIParseError(QAPISourceError):
    """Error class for all QAPI schema parsing errors."""
    def __init__(self, parser, msg):
        col = 1
        for ch in parser.src[parser.line_pos:parser.pos]:
            if ch == '\t':
                col = (col + 7) % 8 + 1
            else:
                col += 1
        super().__init__(parser.info, msg, col)


class QAPISemError(QAPISourceError):
    """Error class for semantic QAPI errors."""
