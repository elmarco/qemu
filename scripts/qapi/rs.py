"""
QAPI Rust generator
"""

import os
import subprocess

from qapi.common import *
from qapi.gen import QAPIGen, QAPISchemaVisitor


rs_name_trans = str.maketrans('.-', '__')

# Map @name to a valid Rust identifier.
# If @protect, avoid returning certain ticklish identifiers (like
# keywords) by prepending raw identifier prefix 'r#'.
def rs_name(name, protect=True):
    name = name.translate(rs_name_trans)
    if name[0].isnumeric():
        name = '_' + name
    if not protect:
        return name
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


def rs_systype(c_type, sys_ns='qapi_sys::'):
    is_pointer = False
    is_const = False
    if c_type.endswith(pointer_suffix):
        is_pointer = True
        c_type = c_type.rstrip(pointer_suffix).strip()

    if c_type.startswith('const '):
        c_type = c_type[6:]
        is_const = True

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

    return rs


def to_camel_case(value):
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


class QAPIGenRs(QAPIGen):

    def __init__(self, fname):
        super().__init__(fname)


class QAPISchemaRsVisitor(QAPISchemaVisitor):

    def __init__(self, prefix, what):
        self._prefix = prefix
        self._what = what
        self._gen = QAPIGenRs(self._prefix + self._what + '.rs')

    def write(self, output_dir):
        self._gen.write(output_dir)

        pathname = os.path.join(output_dir, self._gen.fname)
        try:
            subprocess.check_call(['rustfmt', pathname])
        except FileNotFoundError:
            pass
