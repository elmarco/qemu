#!/usr/bin/env python3

from typing import List, Optional
from .common import c_name, c_enum_const, IfCond, mcgen
from .rs import rs_name
from .schema import (
    QAPISchemaEnumMember,
    QAPISchemaObjectType,
    QAPISchemaObjectTypeMember,
    QAPISchemaVariants,
)


class CABI:
    def __init__(self, name: str, ifcond: IfCond):
        self.name = name
        self.ifcond = ifcond

    def gen_c(self) -> str:
        raise NotImplementedError()

    def gen_rs(self) -> str:
        raise NotImplementedError()


class CABIEnum(CABI):
    def __init__(
        self,
        name: str,
        ifcond: IfCond,
        members: List[QAPISchemaEnumMember],
        prefix: Optional[str] = None,
    ):
        super().__init__(name, ifcond)
        self.members = members
        self.prefix = prefix

    def gen_c(self) -> str:
        last = c_enum_const(self.name, "_MAX", self.prefix)
        ret = self.ifcond.gen_if()
        ret += mcgen("""
    printf("%(name)s enum: sizeof=%%zu\\n", sizeof(%(name)s));
    printf(" max=%%d\\n", %(last)s);
    printf("\\n");
""",
            name=self.name,
            last=last,
        )
        ret += self.ifcond.gen_endif()
        return ret

    def gen_rs(self) -> str:
        return mcgen("""
    %(cfg)s
    {
        println!("%(name)s enum: sizeof={}", ::std::mem::size_of::<%(name)s>());
        println!(" max={}", %(name)s::_MAX as u32);
        println!();
    }
""",
            name=self.name,
            cfg=self.ifcond.gen_rs_cfg(),
        )


class CABIStruct(CABI):
    def __init__(self, name: str, ifcond: IfCond):
        super().__init__(name, ifcond)
        self.members: List[CABIStructMember] = []

    def add_members(self, members: List[QAPISchemaObjectTypeMember]) -> None:
        for memb in members:
            if memb.optional:
                self.add_member(f"has_{c_name(memb.name)}", memb.ifcond)
            self.add_member(c_name(memb.name), memb.ifcond)

    def add_variants(self, variants: Optional[QAPISchemaVariants]) -> None:
        for var in variants.variants:
            if var.type.name == "q_empty":
                continue
            self.add_member("u." + c_name(var.name), var.ifcond)

    def add_member(self, member: str, ifcond: Optional[IfCond] = None) -> None:
        self.members.append(CABIStructMember(self, member, ifcond))

    def gen_c(self) -> str:
        ret = self.ifcond.gen_if()
        ret += mcgen("""
    printf("%(name)s struct: sizeof=%%zu\\n", sizeof(%(name)s));
""",
            name=self.name,
            ifcond=self.ifcond.gen_if(),
        )
        for m in self.members:
            ret += m.gen_c()
        ret += mcgen("""
    printf("\\n");
"""
        )
        ret += self.ifcond.gen_endif()
        return ret

    def gen_rs(self) -> str:
        ret = mcgen("""
    %(cfg)s
    {
        println!("%(name)s struct: sizeof={}", ::std::mem::size_of::<%(name)s>());
""",
            name=self.name,
            cfg=self.ifcond.gen_rs_cfg(),
        )
        for m in self.members:
            ret += m.gen_rs()
        ret += mcgen("""
        println!();
    }
"""
        )
        return ret


class CABIStructMember:
    def __init__(self, struct: CABIStruct, name: str, ifcond: IfCond):
        self.struct = struct
        self.name = name
        self.ifcond = ifcond

    def gen_c(self) -> str:
        ret = self.ifcond.gen_if() if self.ifcond else ""
        ret += mcgen("""
    printf(" %(member)s member: sizeof=%%zu offset=%%zu\\n",
            G_SIZEOF_MEMBER(struct %(sname)s, %(member)s),
            offsetof(struct %(sname)s, %(member)s));
""",
            member=self.name,
            sname=self.struct.name,
        )
        ret += self.ifcond.gen_endif() if self.ifcond else ""
        return ret

    def gen_rs(self) -> str:
        ret = self.ifcond.gen_rs_cfg() if self.ifcond else ""
        if self.name.startswith("u."):
            name = f"u.{rs_name(self.name[2:])}"
        else:
            name = rs_name(self.name)
        ret += mcgen("""
    unsafe {
        println!(" %(member)s member: sizeof={} offset={}",
            ::std::mem::size_of_val(&(*::std::ptr::null::<%(sname)s>()).%(name)s),
            &(*(::std::ptr::null::<%(sname)s>())).%(name)s as *const _ as usize,
        );
    }
""",
            member=self.name,
            name=name,
            sname=self.struct.name,
        )
        return ret


def gen_object_cabi(
    name: str,
    ifcond: IfCond,
    base: Optional[QAPISchemaObjectType],
    members: List[QAPISchemaObjectTypeMember],
    variants: Optional[QAPISchemaVariants],
) -> List[CABI]:
    ret = []
    for var in variants.variants if variants else ():
        obj = var.type
        if not isinstance(obj, QAPISchemaObjectType):
            continue
        ret.extend(
            gen_object_cabi(
                obj.name, obj.ifcond, obj.base, obj.local_members, obj.variants
            )
        )
    cabi = CABIStruct(c_name(name), ifcond)
    if base:
        cabi.add_members(base.members)
    cabi.add_members(members)
    if variants:
        cabi.add_variants(variants)
    if (not base or base.is_empty()) and not members and not variants:
        cabi.add_member("qapi_dummy_for_empty_struct")
    ret.append(cabi)
    return ret
