# This work is licensed under the terms of the GNU GPL, version 2.
# See the COPYING file in the top-level directory.
"""
QAPI Rust types generator
"""

from typing import List, Optional
from .schema import (
    QAPISchema,
    QAPISchemaEnumMember,
    QAPISchemaEnumType,
    QAPISchemaFeature,
    QAPISchemaObjectType,
    QAPISchemaObjectTypeMember,
    QAPISchemaType,
    QAPISchemaVariants,
)
from .source import QAPISourceInfo
from .common import (
    mcgen,
    IfCond,
)
from .rs import *


objects_seen = set()


def gen_rs_variants_enum_kind(name: str,
                              ifcond: IfCond,
                              kind_arms: str) -> str:
    return mcgen('''

%(cfg)s
impl %(rs_name)sEnum {
    pub fn kind(&self) -> %(rs_name)sKind {
        match self {
            %(kind_arms)s
        }
    }
}
''', cfg=ifcond.gen_rs_cfg(), rs_name=rs_name(name), kind_arms=kind_arms)


def gen_rs_variants_to_qemu(name: str,
                            ifcond: IfCond,
                            variants: Optional[QAPISchemaVariants]) -> str:
    ret = mcgen('''

%(cfg)s
pub enum %(rs_name)sCEnum<'a> {
''', cfg=ifcond.gen_rs_cfg(), rs_name=rs_name(name))

    none_arms = ''
    full_arms = ''
    for var in variants.variants:
        var_name = to_camel_case(rs_name(var.name, False))
        type_name = var.type.name
        if type_name == 'q_empty':
            continue
        if type_name.endswith('-wrapper'):
            type_name = type_name[6:-8]
        ret += mcgen('''
    %(cfg)s
    %(var_name)s(<%(rs_type)s as ToQemuPtr<'a, *mut %(rs_systype)s>>::Storage),
''',
                     cfg=var.ifcond.gen_rs_cfg(),
                     var_name=var_name,
                     rs_type=rs_type(type_name, ''),
                     rs_systype=rs_systype(type_name))
        none_arms += mcgen('''
    %(cfg)s
    %(rs_name)sEnum::%(var_name)s(v) => {
        let stash_ = v.to_qemu_none();
        (stash_.0 as *mut std::ffi::c_void, %(rs_name)sCEnum::%(var_name)s(stash_.1))
    },
''',
                           cfg=var.ifcond.gen_rs_cfg(),
                           rs_name=rs_name(name),
                           var_name=var_name)
        full_arms += mcgen('''
    %(cfg)s
    %(rs_name)sEnum::%(var_name)s(v) => {
        let ptr = v.to_qemu_full();
        ptr as *mut std::ffi::c_void
    },
''',
                           cfg=ifcond.gen_rs_cfg(),
                           rs_name=rs_name(name),
                           var_name=var_name)

    ret += mcgen('''
}

%(cfg)s
impl QemuPtrDefault for %(rs_name)sEnum {
    type QemuType = *mut std::ffi::c_void;
}

%(cfg)s
impl<'a> ToQemuPtr<'a, *mut std::ffi::c_void> for %(rs_name)sEnum {
    type Storage = %(rs_name)sCEnum<'a>;

    #[inline]
    fn to_qemu_none(&'a self) -> Stash<'a, *mut std::ffi::c_void, %(rs_name)sEnum> {
        let (ptr_, cenum_) = match self {
             %(none_arms)s
        };

        Stash(ptr_, cenum_)
    }

    #[inline]
    fn to_qemu_full(&self) -> *mut std::ffi::c_void {
        match self {
            %(full_arms)s
        }
    }
}
''',
                 cfg=ifcond.gen_rs_cfg(),
                 rs_name=rs_name(name),
                 none_arms=none_arms,
                 full_arms=full_arms)
    return ret


def gen_rs_variants(name: str,
                    ifcond: IfCond,
                    variants: Optional[QAPISchemaVariants]) -> str:
    ret = mcgen('''

%(cfg)s
#[derive(Clone,Debug)]
pub enum %(rs_name)sEnum {
''',
                cfg=ifcond.gen_rs_cfg(),
                rs_name=rs_name(name))

    kind_arms = ''
    for var in variants.variants:
        type_name = var.type.name
        var_name = to_camel_case(rs_name(var.name, False))
        if type_name == 'q_empty':
            continue
        if type_name.endswith('-wrapper'):
            type_name = type_name[6:-8] # remove q_obj*-wrapper
        kind_arms += mcgen('''
    %(cfg)s
    Self::%(var_name)s(_) => { %(rs_name)sKind::%(var_name)s },
''',
                           cfg=var.ifcond.gen_rs_cfg(),
                           var_name=var_name,
                           rs_name=rs_name(name))
        ret += mcgen('''
    %(cfg)s
    %(var_name)s(%(rs_type)s),
''',
                     cfg=var.ifcond.gen_rs_cfg(),
                     var_name=var_name,
                     rs_type=rs_type(type_name, ''))

    ret += mcgen('''
}
''')

    ret += gen_rs_variants_enum_kind(name, ifcond, kind_arms)
    ret += gen_rs_variants_to_qemu(name, ifcond, variants)
    # TODO FromQemu
    return ret


def gen_rs_object_to_qemu(name: str,
                          ifcond: IfCond,
                          base: Optional[QAPISchemaObjectType],
                          members: List[QAPISchemaObjectTypeMember],
                          variants: Optional[QAPISchemaVariants]) -> str:
    storage = []
    stash = []
    sys_memb = []
    memb_none = ''
    memb_full = ''
    for memb in members:
        memb_name = rs_name(memb.name)
        c_type = memb.type.c_type()
        (is_pointer, _, is_list, _) = rs_ctype_parse(c_type)
        if is_pointer:
            if memb.ifcond:
                raise NotImplementedError("sorry, support missing for members with Stash (file a bug or fix it)")
            t = rs_type(memb.type.c_type(), optional=memb.optional, ns='')
            p = rs_systype(memb.type.c_type(), list_as_newp=True)
            s = "Stash<'a, %s, %s>" % (p, t)
            storage.append(s)
        if memb.optional:
            has_memb_name = 'has_%s' % rs_name(memb.name, protect=False)
            sys_memb.append(f"{memb.ifcond.gen_rs_cfg()} {has_memb_name}")
            has_memb = mcgen('''
    %(cfg)s
    let %(has_memb_name)s = self.%(memb_name)s.is_some();
''',
                             cfg=memb.ifcond.gen_rs_cfg(),
                             memb_name=memb_name,
                             has_memb_name=has_memb_name)
            memb_none += has_memb
            memb_full += has_memb

        if is_pointer:
            stash_name = '{}_stash_'.format(memb_name)
            stash.append(stash_name)
            var = 'NewPtr({})'.format(memb_name) if is_list else memb_name
            memb_none += mcgen('''
    let %(stash_name)s = self.%(memb_name)s.to_qemu_none();
    let %(var)s = %(stash_name)s.0;
''', stash_name=stash_name, memb_name=memb_name, var=var)
            memb_full += mcgen('''
    let %(var)s = self.%(memb_name)s.to_qemu_full();
''', memb_name=memb_name, var=var)
        else:
            unwrap = ''
            if memb.optional:
                unwrap = '.unwrap_or_default()'
            assign = mcgen('''
    %(cfg)s
    let %(memb_name)s = self.%(memb_name)s%(unwrap)s;
''',
                           cfg=memb.ifcond.gen_rs_cfg(),
                           memb_name=memb_name,
                           unwrap=unwrap)
            memb_none += assign
            memb_full += assign

        sys_memb.append(f"{memb.ifcond.gen_rs_cfg()} {memb_name}")

    if variants:
        tag_name = rs_name(variants.tag_member.name)
        sys_memb.append(tag_name)
        sys_memb.append('u')
        p = '*mut std::ffi::c_void'
        s = "Stash<'a, %s, %sEnum>" % (p, name)
        storage.append(s)
        tag = mcgen('''
    let %(tag_name)s = self.u.kind();
''', sys=rs_systype(name), tag_name=tag_name)
        memb_none += tag
        memb_full += tag
        arms = ''
        for variant in variants.variants:
            if variant.type.name == 'q_empty':
                continue
            arms += mcgen('''
    %(cfg)s
    %(rs_name)sEnum::%(kind_name)s(_) => qapi_sys::%(rs_name)sUnion { %(var_name)s: %(var_type)s { data: u_ptr_ as *mut _ } },''',
                          cfg=variant.ifcond.gen_rs_cfg(),
                          rs_name=rs_name(name),
                          kind_name=to_camel_case(variant.name),
                          var_name=rs_name(variant.name),
                          var_type=rs_systype(variant.type.c_name()))
        memb_none += mcgen('''
    let u_stash_ = self.u.to_qemu_none();
    let u_ptr_ = u_stash_.0;
    let u = match self.u {
        %(arms)s
    };
''', arms=arms)
        stash.append('u_stash_')
        memb_full += mcgen('''
    let u_ptr_ = self.u.to_qemu_full();
    let u = match self.u {
        %(arms)s
    };
''', arms=arms)

    return mcgen('''

%(cfg)s
impl QemuPtrDefault for %(rs_name)s {
    type QemuType = *mut qapi_sys::%(rs_name)s;
}

%(cfg)s
impl<'a> ToQemuPtr<'a, *mut qapi_sys::%(rs_name)s> for %(rs_name)s {
    type Storage = (Box<qapi_sys::%(rs_name)s>, %(storage)s);

    #[inline]
    fn to_qemu_none(&'a self) -> Stash<'a, *mut qapi_sys::%(rs_name)s, %(rs_name)s> {
        %(memb_none)s
        let mut box_ = Box::new(qapi_sys::%(rs_name)s { %(sys_memb)s });

        Stash(&mut *box_, (box_, %(stash)s))
    }

    #[inline]
    fn to_qemu_full(&self) -> *mut qapi_sys::%(rs_name)s {
        unsafe {
            %(memb_full)s
            let ptr = sys::g_malloc0(std::mem::size_of::<*const %(rs_name)s>()) as *mut _;
            *ptr = qapi_sys::%(rs_name)s { %(sys_memb)s };
            ptr
        }
    }
}
''',
                 cfg=ifcond.gen_rs_cfg(),
                 rs_name=rs_name(name),
                 storage=', '.join(storage),
                 sys_memb=', '.join(sys_memb),
                 memb_none=memb_none,
                 memb_full=memb_full,
                 stash=', '.join(stash))


def gen_rs_object_from_qemu(name: str,
                            ifcond: IfCond,
                            base: Optional[QAPISchemaObjectType],
                            members: List[QAPISchemaObjectTypeMember],
                            variants: Optional[QAPISchemaVariants]) -> str:
    memb_names = []
    if base:
        memb_names.extend([rs_name(memb.name) for memb in base.members])
    memb_names.extend([f"{m.ifcond.gen_rs_cfg()} {rs_name(m.name)}" for m in members])

    ret = mcgen('''
}

%(cfg)s
impl FromQemuPtrFull<*mut qapi_sys::%(rs_name)s> for %(rs_name)s {
    unsafe fn from_qemu_full(sys: *mut qapi_sys::%(rs_name)s) -> Self {
        let ret = from_qemu_none(sys as *const _);
        qapi_sys::qapi_free_%(rs_name)s(sys);
        ret
    }
}

%(cfg)s
impl FromQemuPtrNone<*const qapi_sys::%(rs_name)s> for %(rs_name)s {
    unsafe fn from_qemu_none(sys: *const qapi_sys::%(rs_name)s) -> Self {
        let sys = & *sys;
''',
                cfg=ifcond.gen_rs_cfg(),
                rs_name=rs_name(name))

    for memb in members:
        memb_name = rs_name(memb.name)
        val = from_qemu('sys.' + memb_name, memb.type.c_type())
        if memb.optional:
            val = mcgen('''{
            if sys.has_%(memb_name)s {
                Some(%(val)s)
            } else {
                None
            }
}''',
                        memb_name=rs_name(memb.name, protect=False),
                        val=val)

        ret += mcgen('''
        %(cfg)s
        let %(memb_name)s = %(val)s;
''',
                     cfg=memb.ifcond.gen_rs_cfg(),
                     memb_name=memb_name,
                     val=val)

    if variants:
        arms = ''
        assert isinstance(variants.tag_member.type, QAPISchemaEnumType)
        for var in variants.tag_member.type.members:
            arms += mcgen('''
            %(cfg)s
            %(enum)s::%(variant)s => { %(rs_name)sEnum::%(variant)s(from_qemu_none(sys.u.%(memb)s.data as *const _)) },
''',
                          cfg=var.ifcond.gen_rs_cfg(),
                          enum=variants.tag_member.type.name,
                          memb=rs_name(var.name),
                          variant=to_camel_case(var.name),
                          rs_name=rs_name(name))
        ret += mcgen('''
        let u = match sys.%(tag)s {
            %(arms)s
            _ => panic!("Variant with invalid tag"),
        };
''',
                     tag=rs_name(variants.tag_member.name),
                     arms=arms)
        memb_names.append('u')

    ret += mcgen('''
            Self { %(memb_names)s }
        }
}
''',
                 memb_names=', '.join(memb_names))
    return ret


def gen_struct_members(members: List[QAPISchemaObjectTypeMember]) -> str:
    ret = ''
    for memb in members:
        ret += mcgen('''
    %(cfg)s
    pub %(rs_name)s: %(rs_type)s,
''',
                     cfg=memb.ifcond.gen_rs_cfg(),
                     rs_type=rs_type(memb.type.c_type(), '', optional=memb.optional),
                     rs_name=rs_name(memb.name))
    return ret


def gen_rs_object(name: str,
                  ifcond: IfCond,
                  base: Optional[QAPISchemaObjectType],
                  members: List[QAPISchemaObjectTypeMember],
                  variants: Optional[QAPISchemaVariants]) -> str:
    if name in objects_seen:
        return ''

    if variants:
        members = [m for m in members if m.name != variants.tag_member.name]

    ret = ''
    objects_seen.add(name)

    if variants:
        ret += gen_rs_variants(name, ifcond, variants)

    ret += mcgen('''
%(cfg)s
#[derive(Clone, Debug)]
pub struct %(rs_name)s {
''',
                 cfg=ifcond.gen_rs_cfg(),
                 rs_name=rs_name(name))

    if base:
        if not base.is_implicit():
            ret += mcgen('''
    // Members inherited:
''',
                         c_name=base.c_name())
        ret += gen_struct_members(base.members)
        if not base.is_implicit():
            ret += mcgen('''
    // Own members:
''')

    ret += gen_struct_members(members)

    if variants:
        ret += mcgen('''
    pub u: %(rs_type)sEnum,
''', rs_type=name)

    ret += gen_rs_object_from_qemu(name, ifcond, base, members, variants)
    ret += gen_rs_object_to_qemu(name, ifcond, base, members, variants)
    return ret


def gen_rs_alternate(name: str,
                     ifcond: IfCond,
                     variants: Optional[QAPISchemaVariants]) -> str:
    if name in objects_seen:
        return ''

    ret = ''
    objects_seen.add(name)

    ret += mcgen('''

%(cfg)s
#[derive(Clone,Debug)]
pub enum %(rs_name)s {
''',
                 cfg=ifcond.gen_rs_cfg(),
                 rs_name=rs_name(name))

    for var in variants.variants:
        if var.type.name == 'q_empty':
            continue
        ret += mcgen('''
        %(cfg)s
        %(mem_name)s(%(rs_type)s),
''',
                     cfg=var.ifcond.gen_rs_cfg(),
                     rs_type=rs_type(var.type.c_unboxed_type(), ''),
                     mem_name=to_camel_case(rs_name(var.name)))
    ret += mcgen('''
}
''')
    # TODO: add to/from conversion
    return ret


def gen_rs_enum(name: str, ifcond: IfCond) -> str:
    return mcgen('''
%(cfg)s
pub type %(rs_name)s = qapi_sys::%(rs_name)s;
''', cfg=ifcond.gen_rs_cfg(), rs_name=rs_name(name))


class QAPISchemaGenRsTypeVisitor(QAPISchemaRsVisitor):

    def __init__(self, prefix: str) -> None:
        super().__init__(prefix, 'qapi-types')

    def visit_begin(self, schema: QAPISchema) -> None:
        # gen_object() is recursive, ensure it doesn't visit the empty type
        objects_seen.add(schema.the_empty_object_type.name)
        self._gen.preamble_add(
            mcgen('''
// generated by qapi-gen, DO NOT EDIT

use common::sys::{QNull, QObject};
use crate::qapi_sys;

'''))

    def visit_array_type(self,
                         name: str,
                         info: Optional[QAPISourceInfo],
                         ifcond: IfCond,
                         element_type: QAPISchemaType) -> None:
        rs = name[:-4]
        if rs in {'str': 'String',
                  'bool': 'bool',
                  'number': 'f64',
                  'int': 'i64',
                  'int8': 'i8',
                  'int16': 'i16',
                  'int32': 'i32',
                  'int64': 'i64',
                  'uint8': 'u8',
                  'uint16': 'u16',
                  'uint32': 'u32',
                  'uint64': 'u64',
                  'size': 'usize',
                  'any': 'QObject',
                  'null': 'QNull',
                  }:
            # FIXME: handle builtin scalar types
            return

        self._gen.add(mcgen('''

vec_from_qemu!(%(rs)s, %(sys)s, qapi_free_%(sys)s);
vec_to_qemu!(%(rs)s, %(sys)s);
''', sys=name, rs=rs))

    def visit_object_type(self,
                          name: str,
                          info: Optional[QAPISourceInfo],
                          ifcond: IfCond,
                          features: List[QAPISchemaFeature],
                          base: Optional[QAPISchemaObjectType],
                          members: List[QAPISchemaObjectTypeMember],
                          variants: Optional[QAPISchemaVariants]) -> None:
        if name.startswith('q_'):
            return
        self._gen.add(gen_rs_object(name, ifcond, base, members, variants))

    def visit_enum_type(self,
                        name: str,
                        info: Optional[QAPISourceInfo],
                        ifcond: IfCond,
                        features: List[QAPISchemaFeature],
                        members: List[QAPISchemaEnumMember],
                        prefix: Optional[str]) -> None:
        self._gen.add(gen_rs_enum(name, ifcond))

    def visit_alternate_type(self,
                             name: str,
                             info: QAPISourceInfo,
                             ifcond: IfCond,
                             features: List[QAPISchemaFeature],
                             variants: QAPISchemaVariants) -> None:
        self._gen.add(gen_rs_alternate(name, ifcond, variants))


def gen_rs_types(schema: QAPISchema, output_dir: str, prefix: str) -> None:
    vis = QAPISchemaGenRsTypeVisitor(prefix)
    schema.visit(vis)
    vis.write(output_dir)
