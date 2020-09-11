#
# QAPI pragma information
#
# Copyright (c) 2020 John Snow, for Red Hat Inc.
#
# Authors:
#  John Snow <jsnow@redhat.com>
#
# This work is licensed under the terms of the GNU GPL, version 2.
# See the COPYING file in the top-level directory.

from typing import List


class QAPISchemaPragma:
    # Replace with @dataclass in Python 3.7+
    # pylint: disable=too-few-public-methods

    def __init__(self) -> None:
        # Are documentation comments required?
        self.doc_required = False
        # Whitelist of commands allowed to return a non-dictionary
        self.returns_whitelist: List[str] = []
        # Whitelist of entities allowed to violate case conventions
        self.name_case_whitelist: List[str] = []
