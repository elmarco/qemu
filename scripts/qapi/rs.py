# This work is licensed under the terms of the GNU GPL, version 2.
# See the COPYING file in the top-level directory.
"""
QAPI Rust generator
"""

import os
import re
import subprocess
from typing import NamedTuple, Optional

from .common import *
from .gen import QAPIGen
from .schema import QAPISchemaVisitor


rs_name_trans = str.maketrans('.-', '__')

# Map @name to a valid Rust identifier.
# If @protect, avoid returning certain ticklish identifiers (like
# keywords) by prepending raw identifier prefix 'r#'.
def rs_name(name: str, protect: bool = True) -> str:
    name = name.translate(rs_name_trans)
    if name[0].isnumeric():
        name = '_' + name
    if not protect:
        return name
    # based from the list:
    # https://doc.rust-lang.org/reference/keywords.html
    if name in ('Self', 'abstract', 'as', 'async',
                'await','become', 'box', 'break',
                'const', 'continue', 'crate', 'do',
                'dyn', 'else', 'enum', 'extern',
                'false', 'final', 'fn', 'for',
                'if', 'impl', 'in', 'let',
                'loop', 'macro', 'match', 'mod',
                'move', 'mut', 'override', 'priv',
                'pub', 'ref', 'return', 'self',
                'static', 'struct', 'super', 'trait',
                'true', 'try', 'type', 'typeof',
                'union', 'unsafe', 'unsized', 'use',
                'virtual', 'where', 'while', 'yield',
                ):
        name = 'r#' + name
    return name


def rs_type(c_type: str,
            ns: Optional[str]='qapi::',
            optional: Optional[bool]=False) -> str:
    vec = False
    to_rs = {
        'char': 'i8',
        'int8_t': 'i8',
        'uint8_t': 'u8',
        'int16_t': 'i16',
        'uint16_t': 'u16',
        'int32_t': 'i32',
        'uint32_t': 'u32',
        'int64_t': 'i64',
        'uint64_t': 'u64',
        'double': 'f64',
        'bool': 'bool',
        'str': 'String',
    }
    if c_type.startswith('const '):
        c_type = c_type[6:]
    if c_type.endswith(POINTER_SUFFIX):
        c_type = c_type.rstrip(POINTER_SUFFIX).strip()
        if c_type.endswith('List'):
            c_type = c_type[:-4]
            vec = True
        else:
            to_rs = {
                'char': 'String',
            }

    if c_type in to_rs:
        ret = to_rs[c_type]
    else:
        ret = ns + c_type

    if vec:
        ret = 'Vec<%s>' % ret
    if optional:
        return 'Option<%s>' % ret
    else:
        return ret


class CType(NamedTuple):
    is_pointer: bool
    is_const: bool
    is_list: bool
    c_type: str


def rs_ctype_parse(c_type: str) -> CType:
    is_pointer = False
    if c_type.endswith(POINTER_SUFFIX):
        is_pointer = True
        c_type = c_type.rstrip(POINTER_SUFFIX).strip()
    is_list = c_type.endswith('List')
    is_const = False
    if c_type.startswith('const '):
        is_const = True
        c_type = c_type[6:]

    return CType(is_pointer, is_const, is_list, c_type)


def rs_systype(c_type: str, sys_ns: str ='qapi_sys::', list_as_newp: bool = False) -> str:
    (is_pointer, is_const, is_list, c_type) = rs_ctype_parse(c_type)

    to_rs = {
        'char': 'libc::c_char',
        'int8_t': 'i8',
        'uint8_t': 'u8',
        'int16_t': 'i16',
        'uint16_t': 'u16',
        'int32_t': 'i32',
        'uint32_t': 'u32',
        'int64_t': 'libc::c_longlong',
        'uint64_t': 'libc::c_ulonglong',
        'double': 'libc::c_double',
        'bool': 'bool',
    }

    rs = ''
    if is_const and is_pointer:
        rs += '*const '
    elif is_pointer:
        rs += '*mut '
    if c_type in to_rs:
        rs += to_rs[c_type]
    else:
        rs += sys_ns + c_type

    if is_list and list_as_newp:
        rs = 'NewPtr<{}>'.format(rs)

    return rs


def to_camel_case(value: str) -> str:
    if value[0] == '_':
        return value
    raw_id = False
    if value.startswith('r#'):
        raw_id = True
        value = value[2:]
    value = ''.join(word.title() for word in filter(None, re.split("[-_]+", value)))
    if raw_id:
        return 'r#' + value
    else:
        return value


def to_qemu_none(c_type: str, name: str) -> str:
    (is_pointer, _, is_list, _) = rs_ctype_parse(c_type)

    if is_pointer:
        if c_type == 'char':
            return mcgen('''
    let %(name)s_ = CString::new(%(name)s).unwrap();
    let %(name)s = %(name)s_.as_ptr();
''', name=name)
        elif is_list:
            return mcgen('''
    let %(name)s_ = NewPtr(%(name)s).to_qemu_none();
    let %(name)s = %(name)s_.0.0;
''', name=name)
        else:
            return mcgen('''
    let %(name)s_ = %(name)s.to_qemu_none();
    let %(name)s = %(name)s_.0;
''', name=name)
    return ''


def from_qemu(var_name: str, c_type: str, full: Optional[bool]=False) -> str:
    (is_pointer, _, is_list, _) = rs_ctype_parse(c_type)
    ptr = '{} as *{} _'.format(var_name, 'mut' if full else 'const')
    if is_list:
        ptr = 'NewPtr({})'.format(ptr)
    if is_pointer:
        return 'from_qemu_{}({})'.format('full' if full else 'none', ptr)
    else:
        return var_name


class QAPIGenRs(QAPIGen):

    def __init__(self, fname: str):
        super().__init__(fname)


class QAPISchemaRsVisitor(QAPISchemaVisitor):

    def __init__(self, prefix: str, what: str):
        super().__init__()
        self._prefix = prefix
        self._what = what
        self._gen = QAPIGenRs(self._prefix + self._what + '.rs')

    def visit_module(self, name: Optional[str]) -> None:
        if name is None:
            return
        assert self._is_user_module(name)
        if self._main_module is None:
            self._main_module = name

    def write(self, output_dir: str) -> None:
        self._gen.write(output_dir)

        pathname = os.path.join(output_dir, self._gen.fname)
        try:
            subprocess.check_call(['rustfmt', pathname])
        except FileNotFoundError:
            pass
