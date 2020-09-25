"""
QAPI Rust generator
"""

import os
import subprocess

from qapi.common import *
from qapi.gen import QAPIGen, QAPISchemaVisitor


from_list = set()

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


def rs_type(c_type, ns='qapi::', optional=False):
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
    if c_type.endswith(pointer_suffix):
        c_type = c_type.rstrip(pointer_suffix).strip()
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


def build_params(arg_type, boxed, typefn=rs_systype, extra=[]):
    ret = []
    if boxed:
        assert arg_type
        ret.append('arg: %s' % typefn(arg_type.c_param_type(const=True)))
    elif arg_type:
        assert not arg_type.variants
        for memb in arg_type.members:
            if memb.optional:
                ret.append('has_%s: bool' % rs_name(c_name(memb.name), protect=False))
            ret.append('%s: %s' % (rs_name(c_name(memb.name)), typefn(memb.type.c_param_type(const=True))))
    ret.extend(extra)
    return ', '.join(ret)


def to_qemu_none(c_type, name):
    is_pointer = False
    is_const = False
    if c_type.endswith(pointer_suffix):
        is_pointer = True
        c_type = c_type.rstrip(pointer_suffix).strip()
        sys_type = rs_systype(c_type)

    if c_type.startswith('const '):
        c_type = c_type[6:]
        is_const = True

    if is_pointer:
        if c_type == 'char':
            return mcgen('''
    let %(name)s_ = CString::new(%(name)s).unwrap();
    let %(name)s = %(name)s_.as_ptr();
''', name=name)
        else:
            return mcgen('''
    let %(name)s_ = %(name)s.to_qemu_none();
    let %(name)s = %(name)s_.0;
''', name=name, sys_type=sys_type)
    return ''


def gen_call(name, arg_type, boxed, ret_type):
    ret = ''

    argstr = ''
    if boxed:
        assert arg_type
        argstr = '&arg, '
    elif arg_type:
        assert not arg_type.variants
        for memb in arg_type.members:
            if memb.optional:
                argstr += 'has_%s, ' % rs_name(c_name(memb.name), protect=False)
            ret += to_qemu_none(memb.type.c_type(), c_name(memb.name))
            argstr += ' %s, ' % rs_name(c_name(memb.name))

    lhs = ''
    if ret_type:
        lhs = 'let retval_ = '

    ret += mcgen('''

%(lhs)sqmp_%(c_name)s(%(args)s&mut err_);
''',
                c_name=c_name(name), args=argstr, lhs=lhs)
    return ret


def from_qemu(var_name, c_type, full=False):
    if c_type.endswith('List' + pointer_suffix):
        from_list.add(c_type)
    is_pointer = c_type.endswith(pointer_suffix)
    if is_pointer:
        if full:
            return 'from_qemu_full(%s as *mut _)' % var_name
        else:
            return 'from_qemu_none(%s as *const _)' % var_name
    else:
        return var_name


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
