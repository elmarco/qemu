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

from typing import TYPE_CHECKING, Optional


if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from .source import QAPISourceInfo


class QAPIError(Exception):
    """Base class for all exceptions from the QAPI module."""


class QAPISourceError(QAPIError):
    """Error class for all exceptions identifying a source location."""
    def __init__(self,
                 info: 'QAPISourceInfo',
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


class QAPISemError(QAPISourceError):
    """Error class for semantic QAPI errors."""
