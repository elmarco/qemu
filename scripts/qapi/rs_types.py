"""
QAPI Rust types generator
"""

from qapi.common import *
from qapi.rs import *


objects_seen = set()


def gen_rs_variants(name, variants):
    ret = mcgen('''

#[derive(Clone,Debug)]
pub enum %(rs_name)sEnum {
''', rs_name=rs_name(name))

    kind_arms = ''
    for var in variants.variants:
        type_name = var.type.name
        var_name = to_camel_case(rs_name(var.name, False))
        if type_name == 'q_empty':
            continue
        if type_name.endswith('-wrapper'):
            type_name = type_name[6:-8]
        kind_arms += mcgen('''
        Self::%(var_name)s(_) => { %(rs_name)sKind::%(var_name)s },
''', var_name=var_name, rs_name=rs_name(name))
        ret += mcgen('''
    %(var_name)s(%(rs_type)s),
''', var_name=var_name, rs_type=rs_type(type_name, ''))

    ret += mcgen('''
}
''')

    ret += mcgen('''

impl %(rs_name)sEnum {
    pub fn kind(&self) -> %(rs_name)sKind {
        match self {
            %(kind_arms)s
        }
    }
}
''', rs_name=rs_name(name), kind_arms=kind_arms)

    ret += mcgen('''

pub enum %(rs_name)sCEnum<'a> {
''', rs_name=rs_name(name))

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
    %(var_name)s(<%(rs_type)s as ToQemuPtr<'a, *mut %(rs_systype)s>>::Storage),
''', var_name=var_name, rs_type=rs_type(type_name, ''), rs_systype=rs_systype(type_name))
        none_arms += mcgen('''
             %(rs_name)sEnum::%(var_name)s(v) => {
                 let stash_ = v.to_qemu_none();
                 (stash_.0 as *mut std::ffi::c_void, %(rs_name)sCEnum::%(var_name)s(stash_.1))
             },
''', rs_name=rs_name(name), var_name=var_name)
        full_arms += mcgen('''
             %(rs_name)sEnum::%(var_name)s(v) => {
                 let ptr = v.to_qemu_full();
                 ptr as *mut std::ffi::c_void
             },
''', rs_name=rs_name(name), var_name=var_name)

    ret += mcgen('''
}

impl translate::QemuPtrDefault for GuestDeviceAddressEnum {
    type QemuType = *mut std::ffi::c_void;
}

impl<'a> translate::ToQemuPtr<'a, *mut std::ffi::c_void> for %(rs_name)sEnum {
    type Storage = %(rs_name)sCEnum<'a>;

    #[inline]
    fn to_qemu_none(&'a self) -> translate::Stash<'a, *mut std::ffi::c_void, %(rs_name)sEnum> {
        let (ptr_, cenum_) = match self {
             %(none_arms)s
        };

        translate::Stash(ptr_, cenum_)
    }

    #[inline]
    fn to_qemu_full(&self) -> *mut std::ffi::c_void {
        match self {
            %(full_arms)s
        }
    }
}
''', rs_name=rs_name(name), none_arms=none_arms, full_arms=full_arms)
    return ret


def gen_struct_members(members):
    ret = ''
    for memb in members:
        rsname = rs_name(memb.name)
        ret += mcgen('''
    pub %(rs_name)s: %(rs_type)s,
''',
                     rs_type=rs_type(memb.type.c_type(), '', optional=memb.optional), rs_name=rsname)
    return ret


def gen_rs_object(name, ifcond, base, members, variants):
    if name in objects_seen:
        return ''

    if variants:
        members = [m for m in members if m.name != variants.tag_member.name]

    ret = ''
    objects_seen.add(name)
    has_options = False
    for memb in members:
        if memb.optional:
            has_options = True

    if variants:
        ret += gen_rs_variants(name, variants)

    ret += mcgen('''

#[derive(Clone, Debug)]
pub struct %(rs_name)s {
''',
                 rs_name=rs_name(name))

    memb_names = []
    if base:
        if not base.is_implicit():
            ret += mcgen('''
    // Members inherited:
''',
                         c_name=base.c_name())
        ret += gen_struct_members(base.members)
        memb_names.extend([rs_name(memb.name) for memb in base.members])
        if not base.is_implicit():
            ret += mcgen('''
    // Own members:
''')

    ret += gen_struct_members(members)
    memb_names.extend([rs_name(memb.name) for memb in members])

    if variants:
        ret += mcgen('''
    pub u: %(rs_type)sEnum,
''', rs_type=name)

    ret += mcgen('''
}

impl FromQemuPtrFull<*mut qapi_sys::%(rs_name)s> for %(rs_name)s {
    unsafe fn from_qemu_full(sys: *mut qapi_sys::%(rs_name)s) -> Self {
        let ret = from_qemu_none(sys as *const _);
        qapi_sys::qapi_free_%(rs_name)s(sys);
        ret
    }
}

impl FromQemuPtrNone<*const qapi_sys::%(rs_name)s> for %(rs_name)s {
    unsafe fn from_qemu_none(sys: *const qapi_sys::%(rs_name)s) -> Self {
        let sys = & *sys;
''', rs_name=rs_name(name))

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
}''', memb_name=rs_name(memb.name, protect=False), val=val)

        ret += mcgen('''
        let %(memb_name)s = %(val)s;
''', memb_name=memb_name, val=val)

    if variants:
        arms = ''
        for variant in variants.tag_member.type.member_names():
            arms += mcgen('''
            %(enum)s::%(variant)s => { %(rs_name)sEnum::%(variant)s(from_qemu_none(sys.u.%(memb)s.data as *const _)) },
''', enum=variants.tag_member.type.name, memb=rs_name(variant),
                          variant=to_camel_case(variant), rs_name=rs_name(name))
        ret += mcgen('''
        let u = match sys.%(tag)s {
            %(arms)s
            _ => panic!("Variant with invalid tag"),
        };
''', tag=rs_name(variants.tag_member.name), arms=arms)
        memb_names.append('u')

    ret += mcgen('''
            Self { %(memb_names)s }
        }
}
''', rs_name=rs_name(name), memb_names=', '.join(memb_names))

    storage = []
    stash = []
    sys_memb = []
    memb_none = ''
    memb_full = ''
    for memb in members:
        memb_name = rs_name(memb.name)
        c_type = memb.type.c_type()
        is_pointer = c_type.endswith(pointer_suffix)
        if is_pointer:
            t = rs_type(memb.type.c_type(), optional=memb.optional, ns='')
            p = rs_systype(memb.type.c_type())
            s = "translate::Stash<'a, %s, %s>" % (p, t)
            storage.append(s)
        if memb.optional:
            has_memb_name = 'has_%s' % rs_name(memb.name, protect=False)
            sys_memb.append(has_memb_name)
            has_memb = mcgen('''
    let %(has_memb_name)s = self.%(memb_name)s.is_some();
''', memb_name=memb_name, has_memb_name=has_memb_name)
            memb_none += has_memb
            memb_full += has_memb

        to_qemu = ''
        if is_pointer:
            memb_none += mcgen('''
    let %(memb_name)s_stash_ = self.%(memb_name)s.to_qemu_none();
    let %(memb_name)s = %(memb_name)s_stash_.0;
''', memb_name=memb_name)
            stash.append('%s_stash_' % memb_name)
            memb_full += mcgen('''
    let %(memb_name)s = self.%(memb_name)s.to_qemu_full();
''', memb_name=memb_name)
        else:
            unwrap = ''
            if memb.optional:
                unwrap = '.unwrap_or_default()'
            memb = mcgen('''
    let %(memb_name)s = self.%(memb_name)s%(unwrap)s;
''', memb_name=memb_name, unwrap=unwrap)
            memb_none += memb
            memb_full += memb

        sys_memb.append(memb_name)

    if variants:
        tag_name = rs_name(variants.tag_member.name)
        sys_memb.append(tag_name)
        sys_memb.append('u')
        p = '*mut std::ffi::c_void'
        s = "translate::Stash<'a, %s, %sEnum>" % (p, name)
        storage.append(s)
        tag = mcgen('''
    let %(tag_name)s = self.u.kind();
''', sys=rs_systype(name), tag_name=tag_name)
        memb_none += tag
        memb_full += tag
        arms = ''
        for var in variants.variants:
            if var.type.name == 'q_empty':
                continue
            arms += mcgen('%(rs_name)sEnum::%(kind_name)s(_) => qapi_sys::%(rs_name)sUnion { %(var_name)s: %(var_type)s { data: u_ptr_ as *mut _ } },',
                          rs_name=rs_name(name), kind_name=to_camel_case(var.name), var_name=rs_name(var.name), var_type=rs_systype(var.type.c_name()))
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
    ret += mcgen('''

impl translate::QemuPtrDefault for %(rs_name)s {
    type QemuType = *mut qapi_sys::%(rs_name)s;
}

impl<'a> translate::ToQemuPtr<'a, *mut qapi_sys::%(rs_name)s> for %(rs_name)s {
    type Storage = (Box<qapi_sys::%(rs_name)s>, %(storage)s);

    #[inline]
    fn to_qemu_none(&'a self) -> translate::Stash<'a, *mut qapi_sys::%(rs_name)s, %(rs_name)s> {
        %(memb_none)s
        let mut box_ = Box::new(qapi_sys::%(rs_name)s { %(sys_memb)s });

        translate::Stash(&mut *box_, (box_, %(stash)s))
    }

    #[inline]
    fn to_qemu_full(&self) -> *mut qapi_sys::%(rs_name)s {
        unsafe {
            %(memb_full)s
            let ptr = qemu_sys::g_malloc0(std::mem::size_of::<*const %(rs_name)s>()) as *mut _;
            *ptr = qapi_sys::%(rs_name)s { %(sys_memb)s };
            ptr
        }
    }
}
''', rs_name=rs_name(name), storage=', '.join(storage),
                 sys_memb=', '.join(sys_memb), memb_none=memb_none, memb_full=memb_full, stash=', '.join(stash))

    return ret


def gen_rs_variant(name, ifcond, variants):
    if name in objects_seen:
        return ''

    ret = ''
    objects_seen.add(name)

    ret += mcgen('''

#[derive(Clone,Debug)]
pub enum %(rs_name)s {
''',
                 rs_name=rs_name(name))

    for var in variants.variants:
        if var.type.name == 'q_empty':
            continue
        ret += mcgen('''
        %(mem_name)s(%(rs_type)s),
''',
                     rs_type=rs_type(var.type.c_unboxed_type(), ''),
                     mem_name=to_camel_case(rs_name(var.name)))
    ret += mcgen('''
}
''')
    return ret


class QAPISchemaGenRsTypeVisitor(QAPISchemaRsVisitor):

    def __init__(self, prefix):
        super().__init__(prefix, 'qapi-types')

    def visit_begin(self, schema):
        # gen_object() is recursive, ensure it doesn't visit the empty type
        objects_seen.add(schema.the_empty_object_type.name)
        self._gen.preamble_add(
            mcgen('''
// generated by qapi-gen, DO NOT EDIT
'''))

    def visit_end(self):
        for c_type in from_list:
            sys = rs_systype(c_type, sys_ns='')[5:]
            rs = rs_type(c_type, ns='')

            self._gen.add(mcgen('''

impl FromQemuPtrFull<*mut qapi_sys::%(sys)s> for %(rs)s {
    #[inline]
    unsafe fn from_qemu_full(sys: *mut qapi_sys::%(sys)s) -> Self {
        let ret = from_qemu_none(sys as *const _);
        qapi_sys::qapi_free_%(sys)s(sys);
        ret
    }
}

impl FromQemuPtrNone<*const qapi_sys::%(sys)s> for %(rs)s {
    #[inline]
    unsafe fn from_qemu_none(sys: *const qapi_sys::%(sys)s) -> Self {
         let mut ret = vec![];
         let mut it = sys;
         while !it.is_null() {
             let e = &*it;
             ret.push(translate::from_qemu_none(e.value as *const _));
             it = e.next;
         }
         ret
    }
}
''', sys=sys, rs=rs))

    def visit_command(self, name, info, ifcond, features,
                      arg_type, ret_type, gen, success_response, boxed,
                      allow_oob, allow_preconfig):
        if not gen:
            return
        # hack: eventually register a from_list
        if ret_type:
            from_qemu('', ret_type.c_type())

    def visit_object_type(self, name, info, ifcond, features,
                          base, members, variants):
        if name.startswith('q_'):
            return
        self._gen.add(gen_rs_object(name, ifcond, base, members, variants))

    def visit_enum_type(self, name, info, ifcond, features, members, prefix):
        self._gen.add(mcgen('''

pub type %(rs_name)s = qapi_sys::%(rs_name)s;
''', rs_name=rs_name(name)))

    def visit_alternate_type(self, name, info, ifcond, features, variants):
        self._gen.add(gen_rs_variant(name, ifcond, variants))


def gen_rs_types(schema, output_dir, prefix, opt_builtins):
    vis = QAPISchemaGenRsTypeVisitor(prefix)
    schema.visit(vis)
    vis.write(output_dir)
