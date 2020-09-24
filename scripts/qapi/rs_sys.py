# This work is licensed under the terms of the GNU GPL, version 2.
# See the COPYING file in the top-level directory.
"""
QAPI Rust sys/ffi generator
"""

from typing import Dict, List, Optional
from .cabi import CABI, CABIEnum, CABIStruct, gen_object_cabi
from .common import *
from .rs import *
from .schema import (
    QAPISchemaEnumMember,
    QAPISchemaObjectType,
    QAPISchemaObjectTypeMember,
    QAPISchemaVariants,
    QAPISchema,
    QAPISchemaFeature,
    QAPISchemaType,
)
from .source import QAPISourceInfo


objects_seen = set()


def gen_rs_sys_enum(name: str,
                    ifcond: IfCond,
                    members: List[QAPISchemaEnumMember],
                    prefix: Optional[str]=None) -> str:
    # append automatically generated _max value
    enum_members = members + [QAPISchemaEnumMember('_MAX', None)]

    ret = mcgen('''

%(cfg)s
#[derive(Copy, Clone, Debug, PartialEq, Eq)]
#[repr(C)]
pub enum %(rs_name)s {
''',
                cfg=ifcond.gen_rs_cfg(),
                rs_name=rs_name(name))

    for m in enum_members:
        ret += mcgen('''
    %(cfg)s
    %(c_enum)s,
''',
                     cfg=m.ifcond.gen_rs_cfg(),
                     c_enum=to_camel_case(rs_name(m.name, False)))
    ret += mcgen('''
}
''')
    return ret


def gen_rs_sys_struct_members(members: List[QAPISchemaObjectTypeMember]) -> str:
    ret = ''
    for memb in members:
        if memb.optional:
            ret += mcgen('''
    %(cfg)s
    pub has_%(rs_name)s: bool,
''',
                         cfg=memb.ifcond.gen_rs_cfg(),
                         rs_name=rs_name(memb.name, protect=False))
        ret += mcgen('''
    %(cfg)s
    pub %(rs_name)s: %(rs_systype)s,
''',
                     cfg=memb.ifcond.gen_rs_cfg(),
                     rs_systype=rs_systype(memb.type.c_type(), ''),
                     rs_name=rs_name(memb.name))
    return ret


def gen_rs_sys_free(ty: str, ifcond: IfCond) -> str:
    return mcgen('''

%(cfg)s
extern "C" {
    pub fn qapi_free_%(ty)s(obj: *mut %(ty)s);
}
''', cfg=ifcond.gen_rs_cfg(), ty=ty)


def gen_rs_sys_variants(name: str,
                        ifcond: IfCond,
                        variants: Optional[QAPISchemaVariants]) -> str:
    ret = mcgen('''

%(cfg)s
#[repr(C)]
#[derive(Copy, Clone)]
pub union %(rs_name)s { /* union tag is @%(tag_name)s */
''',
                cfg=ifcond.gen_rs_cfg(),
                tag_name=rs_name(variants.tag_member.name),
                rs_name=name)

    for var in variants.variants:
        if var.type.name == 'q_empty':
            continue
        ret += mcgen('''
    %(cfg)s
    pub %(rs_name)s: %(rs_systype)s,
''',
                     cfg=var.ifcond.gen_rs_cfg(),
                     rs_systype=rs_systype(var.type.c_unboxed_type(), ''),
                     rs_name=rs_name(var.name))

    ret += mcgen('''
}

%(cfg)s
impl ::std::fmt::Debug for %(rs_name)s {
    fn fmt(&self, f: &mut ::std::fmt::Formatter) -> ::std::fmt::Result {
        f.debug_struct(&format!("%(rs_name)s @ {:?}", self as *const _))
            .finish()
    }
}
''', cfg=ifcond.gen_rs_cfg(), rs_name=name)

    return ret


def gen_rs_sys_object(name: str,
                      ifcond: IfCond,
                      base: Optional[QAPISchemaObjectType],
                      members: List[QAPISchemaObjectTypeMember],
                      variants: Optional[QAPISchemaVariants]) -> str:
    if name in objects_seen:
        return ''

    ret = ''
    objects_seen.add(name)
    unionty = name + 'Union'
    if variants:
        for v in variants.variants:
            if isinstance(v.type, QAPISchemaObjectType):
                ret += gen_rs_sys_object(v.type.name, v.type.ifcond, v.type.base,
                                         v.type.local_members, v.type.variants)
        ret += gen_rs_sys_variants(unionty, ifcond, variants)

    ret += gen_rs_sys_free(rs_name(name), ifcond)
    ret += mcgen('''

%(cfg)s
#[repr(C)]
#[derive(Copy, Clone, Debug)]
pub struct %(rs_name)s {
''',
                 cfg=ifcond.gen_rs_cfg(),
                 rs_name=rs_name(name))

    if base:
        if not base.is_implicit():
            ret += mcgen('''
    // Members inherited:
''')
        ret += gen_rs_sys_struct_members(base.members)
        if not base.is_implicit():
            ret += mcgen('''
    // Own members:
''')

    ret += gen_rs_sys_struct_members(members)
    if variants:
        ret += mcgen('''
        pub u: %(unionty)s
''', unionty=unionty)
    ret += mcgen('''
}
''')
    return ret


def gen_rs_sys_variant(name: str,
                       ifcond: IfCond,
                       variants: Optional[QAPISchemaVariants]) -> str:
    if name in objects_seen:
        return ''

    objects_seen.add(name)

    vs = ''
    for var in variants.variants:
        if var.type.name == 'q_empty':
            continue
        vs += mcgen('''
    %(cfg)s
    pub %(mem_name)s: %(rs_systype)s,
''',
                    cfg=var.ifcond.gen_rs_cfg(),
                    rs_systype=rs_systype(var.type.c_unboxed_type(), ''),
                    mem_name=rs_name(var.name))

    return mcgen('''

%(cfg)s
#[repr(C)]
#[derive(Copy,Clone)]
pub union %(rs_name)sUnion {
    %(variants)s
}

%(cfg)s
impl ::std::fmt::Debug for %(rs_name)sUnion {
    fn fmt(&self, f: &mut ::std::fmt::Formatter) -> ::std::fmt::Result {
        f.debug_struct(&format!("%(rs_name)sUnion @ {:?}", self as *const _))
            .finish()
    }
}

%(cfg)s
#[repr(C)]
#[derive(Copy,Clone,Debug)]
pub struct %(rs_name)s {
    pub %(tag)s: QType,
    pub u: %(rs_name)sUnion,
}
''',
                 cfg=ifcond.gen_rs_cfg(),
                 rs_name=rs_name(name),
                 tag=rs_name(variants.tag_member.name),
                 variants=vs)


def gen_rs_sys_array(name: str,
                     ifcond: IfCond,
                     element_type: QAPISchemaType) -> str:
    ret = mcgen('''

%(cfg)s
#[repr(C)]
#[derive(Copy,Clone)]
pub struct %(rs_name)s {
    pub next: *mut %(rs_name)s,
    pub value: %(rs_systype)s,
}

%(cfg)s
impl ::std::fmt::Debug for %(rs_name)s {
    fn fmt(&self, f: &mut ::std::fmt::Formatter) -> ::std::fmt::Result {
        f.debug_struct(&format!("%(rs_name)s @ {:?}", self as *const _))
            .finish()
    }
}
''',
                cfg=ifcond.gen_rs_cfg(),
                rs_name=rs_name(name), rs_systype=rs_systype(element_type.c_type(), ''))
    ret += gen_rs_sys_free(rs_name(name), ifcond)
    return ret


class QAPISchemaGenRsSysTypeVisitor(QAPISchemaRsVisitor):

    def __init__(self, prefix: str):
        super().__init__(prefix, 'qapi-sys-types')
        self._cabi: Dict[str, CABI] = {}

    def _cabi_add(self, cabis: List[CABI]) -> None:
        for cabi in cabis:
            self._cabi.setdefault(cabi.name, cabi)

    def visit_begin(self, schema: QAPISchema) -> None:
        # gen_object() is recursive, ensure it doesn't visit the empty type
        objects_seen.add(schema.the_empty_object_type.name)
        self._gen.preamble_add(
            mcgen('''
// generated by qapi-gen, DO NOT EDIT

use common::sys::{QNull, QObject};

'''))

    def visit_module_end(self, name: Optional[str]) -> None:
        cabi_gen = "".join([c.gen_rs() for _, c in sorted(self._cabi.items())])
        self._cabi = {}
        fn_name = 'cabi'
        if self.is_builtin_module(name):
            fn_name += '_builtin'
        elif not self.is_main_module(name):
            import os.path
            name = os.path.splitext(name)[0]
            fn_name += '_' + rs_name(name)
        self._gen.add(mcgen('''
#[cfg(QAPI_CABI)]
pub(crate) fn %(fn_name)s() {
%(cabi_gen)s
}
''', fn_name=fn_name, cabi_gen=cabi_gen))

    def visit_enum_type(self,
                        name: str,
                        info: Optional[QAPISourceInfo],
                        ifcond: IfCond,
                        features: List['QAPISchemaFeature'],
                        members: List['QAPISchemaEnumMember'],
                        prefix: Optional[str]) -> None:
        self._gen.add(gen_rs_sys_enum(name, ifcond, members, prefix))
        self._cabi_add([CABIEnum(name, ifcond, members, prefix)])

    def visit_array_type(self,
                         name: str,
                         info: Optional[QAPISourceInfo],
                         ifcond: IfCond,
                         element_type: QAPISchemaType) -> None:
        self._gen.add(gen_rs_sys_array(name, ifcond, element_type))

    def visit_object_type(self,
                          name: str,
                          info: Optional[QAPISourceInfo],
                          ifcond: IfCond,
                          features: List['QAPISchemaFeature'],
                          base: Optional['QAPISchemaObjectType'],
                          members: List['QAPISchemaObjectTypeMember'],
                          variants: Optional['QAPISchemaVariants']) -> None:
        # Nothing to do for the special empty builtin
        if name == 'q_empty':
            return
        self._gen.add(gen_rs_sys_object(name, ifcond, base, members, variants))
        self._cabi_add(gen_object_cabi(name, ifcond, base, members, variants))

    def visit_alternate_type(self,
                             name: str,
                             info: QAPISourceInfo,
                             ifcond: IfCond,
                             features: List['QAPISchemaFeature'],
                             variants: 'QAPISchemaVariants') -> None:
        self._gen.add(gen_rs_sys_variant(name, ifcond, variants))
        self._cabi_add(gen_object_cabi(name, ifcond, None,
                                       [variants.tag_member], variants))


def gen_rs_systypes(schema: QAPISchema,
                    output_dir: str,
                    prefix: str,
                    opt_builtins: bool) -> None:
    vis = QAPISchemaGenRsSysTypeVisitor(prefix)
    schema.visit(vis)
    vis.write(output_dir)
