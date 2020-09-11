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

from typing import Mapping, Sequence

from .error import QAPIError


class PragmaError(QAPIError):
    """For errors relating to Pragma validation."""


class QAPISchemaPragma:
    def __init__(self) -> None:
        # Are documentation comments required?
        self.doc_required = False
        # Whitelist of commands allowed to return a non-dictionary
        self.returns_whitelist: Sequence[str] = tuple()
        # Whitelist of entities allowed to violate case conventions
        self.name_case_whitelist: Sequence[str] = tuple()

    def _add_doc_required(self, value: object) -> None:
        if not isinstance(value, bool):
            raise PragmaError("pragma 'doc-required' must be boolean")
        self.doc_required = value

    def _add_returns_whitelist(self, value: object) -> None:
        if (not isinstance(value, list)
                or any([not isinstance(elt, str) for elt in value])):
            raise PragmaError(
                "pragma returns-whitelist must be a list of strings")
        self.returns_whitelist = tuple(value)

    def _add_name_case_whitelist(self, value: object) -> None:
        if (not isinstance(value, list)
                or any([not isinstance(elt, str) for elt in value])):
            raise PragmaError(
                "pragma name-case-whitelist must be a list of strings")
        self.name_case_whitelist = tuple(value)

    def add(self, name: str, value: object) -> None:
        if name == 'doc-required':
            self._add_doc_required(value)
        elif name == 'returns-whitelist':
            self._add_returns_whitelist(value)
        elif name == 'name-case-whitelist':
            self._add_name_case_whitelist(value)
        else:
            raise PragmaError(f"unknown pragma '{name}'")

    def parse(self, expression: Mapping[str, object]) -> None:
        if expression.keys() != {'pragma'}:
            raise PragmaError("invalid 'pragma' directive")

        body = expression['pragma']
        if not isinstance(body, dict):
            raise PragmaError("value of 'pragma' must be an object")

        for name, value in body.items():
            self.add(name, value)
