# -*- coding: utf-8 -*-
#
# QAPI schema parser
#
# Copyright IBM, Corp. 2011
# Copyright (c) 2013-2019 Red Hat Inc.
#
# Authors:
#  Anthony Liguori <aliguori@us.ibm.com>
#  Markus Armbruster <armbru@redhat.com>
#  Marc-André Lureau <marcandre.lureau@redhat.com>
#  Kevin Wolf <kwolf@redhat.com>
#
# This work is licensed under the terms of the GNU GPL, version 2.
# See the COPYING file in the top-level directory.

from collections import OrderedDict
import os
import re
from typing import (
    List,
    NamedTuple,
    Optional,
    Set,
    Type,
    TypeVar,
    Union,
)

from .error import QAPIError, QAPISemError, QAPISourceError
from .pragma import PragmaError
from .source import QAPISourceInfo


_Value = Union[List[object], 'OrderedDict[str, object]', str, bool]
# Necessary imprecision: mypy does not (yet?) support recursive types;
# so we must stub out that recursion with 'object'.
# Note, we do not support numerics or null in this parser.


class ParsedExpression(NamedTuple):
    expr: 'OrderedDict[str, object]'
    info: QAPISourceInfo
    doc: Optional['QAPIDoc']


class QAPIParseError(QAPISourceError):
    """Error class for all QAPI schema parsing errors."""
    T = TypeVar('T', bound='QAPIParseError')

    @classmethod
    def make(cls: Type[T], parser: 'QAPISchemaParser', msg: str) -> T:
        col = 1
        for ch in parser.src[parser.line_pos:parser.pos]:
            if ch == '\t':
                col = (col + 7) % 8 + 1
            else:
                col += 1
        return cls(parser.info, msg, col)


class QAPIDocError(QAPIError):
    """Documentation parsing error."""


class QAPISchemaParser:
    """
    Performs parsing of a QAPI schema source file.

    :param fname:  Path to the source file
    :param parent: Parent parser, if this is an included file.
    """
    def __init__(self, fname: str,
                 parent: Optional['QAPISchemaParser'] = None):
        self._fname = fname
        self._included: Set[str] = parent._included if parent else set()
        self._included.add(os.path.abspath(self._fname))
        parent_info = parent.info if parent else None

        # Lexer state (see `accept` for details):
        self.tok: Optional[str] = None
        self.pos = 0
        self.cursor = 0
        self.val: Optional[Union[bool, str]] = None
        self.info: QAPISourceInfo = QAPISourceInfo(self._fname,
                                                   parent=parent_info)
        self.line_pos = 0

        # Parser output:
        self.exprs: List[ParsedExpression] = []
        self.docs: List[QAPIDoc] = []

        # Showtime!
        try:
            with open(self._fname, 'r', encoding='utf-8') as fp:
                self.src = fp.read()
        except IOError as e:
            msg = "can't read {kind:s} file '{fname:s}': {errmsg:s}".format(
                kind='include' if parent else 'schema',
                fname=self._fname,
                errmsg=e.strerror
            )
            context = parent_info if parent_info else self.info
            raise QAPIParseError(context, msg) from e
        self._parse()

    def _parse(self) -> None:
        """
        Parse the QAPI Schema Document.
        Build self.exprs, self.docs
        """
        cur_doc = None

        # Prime the lexer:
        self.info.line += 1
        if self.src == '' or self.src[-1] != '\n':
            self.src += '\n'
        self.accept()

        while self.tok is not None:
            info = self.info
            if self.tok == '#':
                self.reject_expr_doc(cur_doc)
                for cur_doc in self.get_doc(info):
                    self.docs.append(cur_doc)
                continue

            expr = self.get_expr(False)
            if not isinstance(expr, dict):
                raise QAPISemError(info, "Expecting object statement")

            if 'include' in expr:
                self.reject_expr_doc(cur_doc)
                if len(expr) != 1:
                    raise QAPISemError(info, "invalid 'include' directive")
                include = expr['include']
                if not isinstance(include, str):
                    raise QAPISemError(info,
                                       "value of 'include' must be a string")
                incl_fname = os.path.join(os.path.dirname(self._fname),
                                          include)
                self._add_expr(OrderedDict({'include': incl_fname}), info)
                exprs_include = self._include(include, incl_fname)
                if exprs_include:
                    self.exprs.extend(exprs_include.exprs)
                    self.docs.extend(exprs_include.docs)
            elif "pragma" in expr:
                self.reject_expr_doc(cur_doc)
                try:
                    info.pragma.parse(expr)
                except PragmaError as err:
                    raise QAPISemError(info, str(err)) from err
            else:
                if cur_doc and not cur_doc.symbol:
                    raise QAPISemError(
                        cur_doc.info, "definition documentation required")
                self._add_expr(expr, info, cur_doc)
            cur_doc = None
        self.reject_expr_doc(cur_doc)

    def _parse_error(self, msg: str) -> QAPIParseError:
        return QAPIParseError.make(self, msg)

    def _add_expr(self, expr: 'OrderedDict[str, object]',
                  info: QAPISourceInfo,
                  doc: Optional['QAPIDoc'] = None) -> None:
        self.exprs.append(ParsedExpression(expr, info, doc))

    @classmethod
    def reject_expr_doc(cls, doc: Optional['QAPIDoc']) -> None:
        if doc and doc.symbol:
            raise QAPISemError(
                doc.info,
                "documentation for '%s' is not followed by the definition"
                % doc.symbol)

    def _include(self, include: str,
                 incl_fname: str) -> Optional['QAPISchemaParser']:
        incl_abs_fname = os.path.abspath(incl_fname)

        # catch inclusion cycle
        inf = self.info
        while inf:
            if incl_abs_fname == os.path.abspath(inf.fname):
                raise QAPISemError(self.info, f"inclusion loop for {include}")
            inf = inf.parent

        # skip multiple include of the same file
        if incl_abs_fname in self._included:
            return None

        return QAPISchemaParser(incl_fname, self)

    def accept(self, skip_comment: bool = True) -> None:
        """Read the next lexeme.

        :State:
          :tok:    is the current lexeme/token type.
          :pos:    is the position of the first character in the lexeme.
          :cursor: is the position of the next character.
          :val:    is the value of the lexeme (if any).

        Single-character lexemes:

        These include ``LBRACE``, ``RBRACE``, ``COLON``, ``COMMA``, ``LSQB``,
        and ``RSQB``. ``tok`` holds the single-char representing the lexeme.
        ``val`` is ``None``.

        Multi-character lexemes:

        ``COMMENT``:

          - ``tok`` is ``'#'``.
          - ``val`` is a string including all chars until end-of-line.

        ``STRING``:

          - ``tok`` is ``"'"``.
          - ``value`` is the string, excluding the quotes.

        ``TRUE`` and ``FALSE``:

          - ``tok`` is either ``"t"`` or ``"f"`` accordingly.
          - ``val`` is either ``True`` or ``False`` accordingly.

        ``NEWLINE`` and ``SPACE``:
          These are consumed by the lexer directly. ``line_pos`` and ``info``
          are advanced when ``NEWLINE`` is encountered. ``tok`` is set to
          ``None`` upon reaching EOF.
        """
        while True:
            self.tok = self.src[self.cursor]
            self.pos = self.cursor
            self.cursor += 1
            self.val = None

            if self.tok == '#':
                if self.src[self.cursor] == '#':
                    # Start of doc comment
                    skip_comment = False
                self.cursor = self.src.find('\n', self.cursor)
                if not skip_comment:
                    self.val = self.src[self.pos:self.cursor]
                    return
            elif self.tok in '{}:,[]':
                return
            elif self.tok == "'":
                # Note: we accept only printable ASCII
                string = ''
                esc = False
                while True:
                    ch = self.src[self.cursor]
                    self.cursor += 1
                    if ch == '\n':
                        raise self._parse_error("missing terminating \"'\"")
                    if esc:
                        # Note: we recognize only \\ because we have
                        # no use for funny characters in strings
                        if ch != '\\':
                            raise self._parse_error(f"unknown escape \\{ch}")
                        esc = False
                    elif ch == '\\':
                        esc = True
                        continue
                    elif ch == "'":
                        self.val = string
                        return
                    if ord(ch) < 32 or ord(ch) >= 127:
                        raise self._parse_error("funny character in string")
                    string += ch
            elif self.src.startswith('true', self.pos):
                self.val = True
                self.cursor += 3
                return
            elif self.src.startswith('false', self.pos):
                self.val = False
                self.cursor += 4
                return
            elif self.tok == '\n':
                if self.cursor == len(self.src):
                    self.tok = None
                    return
                self.info = self.info.next_line()
                self.line_pos = self.cursor
            elif not self.tok.isspace():
                # Show up to next structural, whitespace or quote
                # character
                match = re.match('[^[\\]{}:,\\s\'"]+',
                                 self.src[self.cursor-1:])
                raise self._parse_error("stray '%s'" % match.group(0))

    def get_members(self) -> 'OrderedDict[str, object]':
        expr: 'OrderedDict[str, object]' = OrderedDict()
        if self.tok == '}':
            self.accept()
            return expr
        if self.tok != "'":
            raise self._parse_error("expected string or '}'")
        while True:
            key = self.val
            assert isinstance(key, str), f"expected str, got {type(key)!s}"

            self.accept()
            if self.tok != ':':
                raise self._parse_error("expected ':'")
            self.accept()
            if key in expr:
                raise self._parse_error("duplicate key '%s'" % key)
            expr[key] = self.get_expr(True)
            if self.tok == '}':
                self.accept()
                return expr
            if self.tok != ',':
                raise self._parse_error("expected ',' or '}'")
            self.accept()
            if self.tok != "'":
                raise self._parse_error("expected string")

    def get_values(self) -> List[object]:
        expr: List[object] = []
        if self.tok == ']':
            self.accept()
            return expr
        if self.tok not in "{['tf":
            raise self._parse_error(
                "expected '{', '[', ']', string, or boolean")
        while True:
            expr.append(self.get_expr(True))
            if self.tok == ']':
                self.accept()
                return expr
            if self.tok != ',':
                raise self._parse_error("expected ',' or ']'")
            self.accept()

    def get_expr(self, nested: bool = False) -> _Value:
        expr: _Value
        if self.tok != '{' and not nested:
            raise self._parse_error("expected '{'")
        if self.tok == '{':
            self.accept()
            expr = self.get_members()
        elif self.tok == '[':
            self.accept()
            expr = self.get_values()
        elif self.tok in "'tf":
            expr = self.val
            self.accept()
        else:
            raise self._parse_error(
                "expected '{', '[', string, or boolean")
        return expr

    def _get_doc(self, info: QAPISourceInfo) -> List['QAPIDoc']:
        if self.val != '##':
            raise self._parse_error(
                "junk after '##' at start of documentation comment")

        docs = []
        cur_doc = QAPIDoc(info)
        self.accept(False)
        while self.tok == '#':
            assert isinstance(self.val, str), "Expected str value"
            if self.val.startswith('##'):
                # End of doc comment
                if self.val != '##':
                    raise self._parse_error(
                        "junk after '##' at end of documentation comment")
                cur_doc.end_comment()
                docs.append(cur_doc)
                self.accept()
                return docs
            if self.val.startswith('# ='):
                if cur_doc.symbol:
                    raise self._parse_error(
                        "unexpected '=' markup in definition documentation")
                if cur_doc.body.text:
                    cur_doc.end_comment()
                    docs.append(cur_doc)
                    cur_doc = QAPIDoc(info)
            cur_doc.append(self.val)
            self.accept(False)

        raise self._parse_error("documentation comment must end with '##'")

    def get_doc(self, info: QAPISourceInfo) -> List['QAPIDoc']:
        try:
            return self._get_doc(info)
        except QAPIDocError as err:
            # Tie the Doc parsing error to our parsing state. The
            # resulting error position depends on the state of the
            # parser. It happens to be the beginning of the comment.
            # More or less servicable, but action at a distance.
            raise self._parse_error(str(err)) from err


class QAPIDoc:
    """
    A documentation comment block, either definition or free-form

    Definition documentation blocks consist of

    * a body section: one line naming the definition, followed by an
      overview (any number of lines)

    * argument sections: a description of each argument (for commands
      and events) or member (for structs, unions and alternates)

    * features sections: a description of each feature flag

    * additional (non-argument) sections, possibly tagged

    Free-form documentation blocks consist only of a body section.
    """

    class Section:
        def __init__(self, name=None, indent=0):
            # optional section name (argument/member or section name)
            self.name = name
            self.text = ''
            # the expected indent level of the text of this section
            self._indent = indent

        def append(self, line):
            # Strip leading spaces corresponding to the expected indent level
            # Blank lines are always OK.
            if line:
                indent = re.match(r'\s*', line).end()
                if indent < self._indent:
                    raise QAPIDocError(
                        "unexpected de-indent "
                        f"(expected at least {self._indent} spaces)"
                    )
                line = line[self._indent:]

            self.text += line.rstrip() + '\n'

    class ArgSection(Section):
        def __init__(self, name, indent=0):
            super().__init__(name, indent)
            self.member = None

        def connect(self, member):
            self.member = member

    def __init__(self, info):
        self.info = info
        self.symbol = None
        self.body = QAPIDoc.Section()
        # dict mapping parameter name to ArgSection
        self.args = OrderedDict()
        self.features = OrderedDict()
        # a list of Section
        self.sections = []
        # the current section
        self._section = self.body
        self._append_line = self._append_body_line

    def has_section(self, name):
        """Return True if we have a section with this name."""
        for i in self.sections:
            if i.name == name:
                return True
        return False

    def append(self, line):
        """
        Parse a comment line and add it to the documentation.

        The way that the line is dealt with depends on which part of
        the documentation we're parsing right now:
        * The body section: ._append_line is ._append_body_line
        * An argument section: ._append_line is ._append_args_line
        * A features section: ._append_line is ._append_features_line
        * An additional section: ._append_line is ._append_various_line
        """
        line = line[1:]
        if not line:
            self._append_freeform(line)
            return

        if line[0] != ' ':
            raise QAPIDocError("missing space after #")
        line = line[1:]
        self._append_line(line)

    def end_comment(self):
        self._end_section()

    @classmethod
    def _is_section_tag(cls, name):
        return name in ('Returns:', 'Since:',
                        # those are often singular or plural
                        'Note:', 'Notes:',
                        'Example:', 'Examples:',
                        'TODO:')

    def _append_body_line(self, line):
        """
        Process a line of documentation text in the body section.

        If this a symbol line and it is the section's first line, this
        is a definition documentation block for that symbol.

        If it's a definition documentation block, another symbol line
        begins the argument section for the argument named by it, and
        a section tag begins an additional section.  Start that
        section and append the line to it.

        Else, append the line to the current section.
        """
        name = line.split(' ', 1)[0]
        # FIXME not nice: things like '#  @foo:' and '# @foo: ' aren't
        # recognized, and get silently treated as ordinary text
        if not self.symbol and not self.body.text and line.startswith('@'):
            if not line.endswith(':'):
                raise QAPIDocError("line should end with ':'")
            self.symbol = line[1:-1]
            # FIXME invalid names other than the empty string aren't flagged
            if not self.symbol:
                raise QAPIDocError("invalid name")
        elif self.symbol:
            # This is a definition documentation block
            if name.startswith('@') and name.endswith(':'):
                self._append_line = self._append_args_line
                self._append_args_line(line)
            elif line == 'Features:':
                self._append_line = self._append_features_line
            elif self._is_section_tag(name):
                self._append_line = self._append_various_line
                self._append_various_line(line)
            else:
                self._append_freeform(line)
        else:
            # This is a free-form documentation block
            self._append_freeform(line)

    def _append_args_line(self, line):
        """
        Process a line of documentation text in an argument section.

        A symbol line begins the next argument section, a section tag
        section or a non-indented line after a blank line begins an
        additional section.  Start that section and append the line to
        it.

        Else, append the line to the current section.

        """
        name = line.split(' ', 1)[0]

        if name.startswith('@') and name.endswith(':'):
            # If line is "@arg:   first line of description", find
            # the index of 'f', which is the indent we expect for any
            # following lines.  We then remove the leading "@arg:"
            # from line and replace it with spaces so that 'f' has the
            # same index as it did in the original line and can be
            # handled the same way we will handle following lines.
            indent = re.match(r'@\S*:\s*', line).end()
            line = line[indent:]
            if not line:
                # Line was just the "@arg:" header; following lines
                # are not indented
                indent = 0
            else:
                line = ' ' * indent + line
            self._start_args_section(name[1:-1], indent)
        elif self._is_section_tag(name):
            self._append_line = self._append_various_line
            self._append_various_line(line)
            return
        elif (self._section.text.endswith('\n\n')
              and line and not line[0].isspace()):
            if line == 'Features:':
                self._append_line = self._append_features_line
            else:
                self._start_section()
                self._append_line = self._append_various_line
                self._append_various_line(line)
            return

        self._append_freeform(line)

    def _append_features_line(self, line):
        name = line.split(' ', 1)[0]

        if name.startswith('@') and name.endswith(':'):
            # If line is "@arg:   first line of description", find
            # the index of 'f', which is the indent we expect for any
            # following lines.  We then remove the leading "@arg:"
            # from line and replace it with spaces so that 'f' has the
            # same index as it did in the original line and can be
            # handled the same way we will handle following lines.
            indent = re.match(r'@\S*:\s*', line).end()
            line = line[indent:]
            if not line:
                # Line was just the "@arg:" header; following lines
                # are not indented
                indent = 0
            else:
                line = ' ' * indent + line
            self._start_features_section(name[1:-1], indent)
        elif self._is_section_tag(name):
            self._append_line = self._append_various_line
            self._append_various_line(line)
            return
        elif (self._section.text.endswith('\n\n')
              and line and not line[0].isspace()):
            self._start_section()
            self._append_line = self._append_various_line
            self._append_various_line(line)
            return

        self._append_freeform(line)

    def _append_various_line(self, line):
        """
        Process a line of documentation text in an additional section.

        A symbol line is an error.

        A section tag begins an additional section.  Start that
        section and append the line to it.

        Else, append the line to the current section.
        """
        name = line.split(' ', 1)[0]

        if name.startswith('@') and name.endswith(':'):
            raise QAPIDocError("'%s' can't follow '%s' section"
                               % (name, self.sections[0].name))
        if self._is_section_tag(name):
            # If line is "Section:   first line of description", find
            # the index of 'f', which is the indent we expect for any
            # following lines.  We then remove the leading "Section:"
            # from line and replace it with spaces so that 'f' has the
            # same index as it did in the original line and can be
            # handled the same way we will handle following lines.
            indent = re.match(r'\S*:\s*', line).end()
            line = line[indent:]
            if not line:
                # Line was just the "Section:" header; following lines
                # are not indented
                indent = 0
            else:
                line = ' ' * indent + line
            self._start_section(name[:-1], indent)

        self._append_freeform(line)

    def _start_symbol_section(self, symbols_dict, name, indent):
        # FIXME invalid names other than the empty string aren't flagged
        if not name:
            raise QAPIDocError("invalid parameter name")
        if name in symbols_dict:
            raise QAPIDocError("'%s' parameter name duplicated" % name)
        assert not self.sections
        self._end_section()
        self._section = QAPIDoc.ArgSection(name, indent)
        symbols_dict[name] = self._section

    def _start_args_section(self, name, indent):
        self._start_symbol_section(self.args, name, indent)

    def _start_features_section(self, name, indent):
        self._start_symbol_section(self.features, name, indent)

    def _start_section(self, name=None, indent=0):
        if name in ('Returns', 'Since') and self.has_section(name):
            raise QAPIDocError("duplicated '%s' section" % name)
        self._end_section()
        self._section = QAPIDoc.Section(name, indent)
        self.sections.append(self._section)

    def _end_section(self):
        if self._section:
            text = self._section.text = self._section.text.strip()
            if self._section.name and (not text or text.isspace()):
                raise QAPIDocError(
                    "empty doc section '%s'" % self._section.name)
            self._section = None

    def _append_freeform(self, line):
        match = re.match(r'(@\S+:)', line)
        if match:
            raise QAPIDocError("'%s' not allowed in free-form documentation"
                               % match.group(1))
        self._section.append(line)

    def connect_member(self, member):
        if member.name not in self.args:
            # Undocumented TODO outlaw
            self.args[member.name] = QAPIDoc.ArgSection(member.name)
        self.args[member.name].connect(member)

    def connect_feature(self, feature):
        if feature.name not in self.features:
            raise QAPISemError(feature.info,
                               "feature '%s' lacks documentation"
                               % feature.name)
        self.features[feature.name].connect(feature)

    def check_expr(self, expr):
        if self.has_section('Returns') and 'command' not in expr:
            raise QAPISemError(self.info,
                               "'Returns:' is only valid for commands")

    def check(self):

        def check_args_section(args):
            bogus = [name for name, section in args.items()
                     if not section.member]
            if bogus:
                raise QAPISemError(
                    self.info,
                    "documented member%s '%s' %s not exist"
                    % ("s" if len(bogus) > 1 else "",
                       "', '".join(bogus),
                       "do" if len(bogus) > 1 else "does"))

        check_args_section(self.args)
        check_args_section(self.features)
