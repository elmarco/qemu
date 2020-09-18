# -*- coding: utf-8 -*-
#
# QAPI schema internal representation
#
# Copyright (c) 2015-2019 Red Hat Inc.
#
# Authors:
#  Markus Armbruster <armbru@redhat.com>
#  Eric Blake <eblake@redhat.com>
#  Marc-André Lureau <marcandre.lureau@redhat.com>
#
# This work is licensed under the terms of the GNU GPL, version 2.
# See the COPYING file in the top-level directory.

# pylint: disable=too-many-lines ¯\_(ツ)_/¯

# TODO catching name collisions in generated code would be nice

from collections import OrderedDict
import os
import re
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
    cast,
    overload,
)

from .common import POINTER_SUFFIX, c_name
from .error import QAPISemError, QAPISourceError
from .expr import check_exprs
from .parser import ParsedExpression, QAPIDoc, QAPISchemaParser
from .source import QAPISourceInfo


class Visitable:
    """Abstract duck that suggests a class is visitable."""
    # pylint: disable=too-few-public-methods

    def visit(self, visitor: 'QAPISchemaVisitor') -> None:
        raise NotImplementedError


class QAPISchemaEntity(Visitable):
    def __init__(self,
                 name: str,
                 info: Optional[QAPISourceInfo],
                 doc: Optional[QAPIDoc],
                 ifcond: Optional[Union[List[str], 'QAPISchemaType']] = None,
                 features: Optional[List['QAPISchemaFeature']] = None):
        assert name is None or isinstance(name, str)

        for feature in features or []:
            assert isinstance(feature, QAPISchemaFeature)
            feature.set_defined_in(name)

        self.name = name
        self._module: Optional[QAPISchemaModule] = None
        # For explicitly defined entities, info points to the (explicit)
        # definition.  For builtins (and their arrays), info is None.
        # For implicitly defined entities, info points to a place that
        # triggered the implicit definition (there may be more than one
        # such place).
        self.info = info
        self.doc = doc
        self._ifcond = ifcond or []
        self.features = features or []
        self._checked = False
        self._meta = ''

    @property
    def meta(self) -> str:
        return self._meta

    @meta.setter
    def meta(self, value: str) -> None:
        self._meta = value

    def c_name(self) -> str:
        return c_name(self.name)

    def check(self, schema: 'QAPISchema') -> None:
        # pylint: disable=unused-argument
        assert not self._checked
        seen: Dict[str, 'QAPISchemaMember'] = {}
        for feature in self.features:
            feature.check_clash(self.info, seen)
        self._checked = True

    def connect_doc(self, doc: Optional[QAPIDoc] = None) -> None:
        doc = doc or self.doc
        if doc:
            for feature in self.features:
                doc.connect_feature(feature)

    def check_doc(self) -> None:
        if self.doc:
            self.doc.check()

    def _set_module(self,
                    schema: 'QAPISchema',
                    info: Optional[QAPISourceInfo]) -> None:
        assert self._checked
        self._module = schema.module_by_fname(info.fname if info else None)
        self._module.add_entity(self)

    def set_module(self, schema: 'QAPISchema') -> None:
        self._set_module(schema, self.info)

    @property
    def ifcond(self) -> List[str]:
        assert self._checked and isinstance(self._ifcond, list)
        return self._ifcond

    def is_implicit(self) -> bool:
        return not self.info

    def visit(self, visitor: 'QAPISchemaVisitor') -> None:
        assert self._checked

    def describe(self) -> str:
        assert self.meta
        return "%s '%s'" % (self.meta, self.name)


class QAPISchemaVisitor:
    def visit_begin(self, schema: 'QAPISchema') -> None:
        pass

    def visit_end(self) -> None:
        pass

    def visit_module(self, name: Optional[str]) -> None:
        pass

    def visit_needed(self, entity: QAPISchemaEntity) -> bool:
        # pylint: disable=unused-argument, no-self-use
        # Default to visiting everything
        return True

    def visit_include(self, name: str, info: QAPISourceInfo) -> None:
        pass

    def visit_builtin_type(self, name: str,
                           info: Optional[QAPISourceInfo],
                           json_type: str) -> None:
        pass

    def visit_enum_type(self,
                        name: str,
                        info: Optional[QAPISourceInfo],
                        ifcond: List[str],
                        features: List['QAPISchemaFeature'],
                        members: List['QAPISchemaEnumMember'],
                        prefix: Optional[str]) -> None:
        pass

    def visit_array_type(self,
                         name: str,
                         info: Optional[QAPISourceInfo],
                         ifcond: List[str],
                         element_type: 'QAPISchemaType') -> None:
        pass

    def visit_object_type(self,
                          name: str,
                          info: Optional[QAPISourceInfo],
                          ifcond: List[str],
                          features: List['QAPISchemaFeature'],
                          base: Optional['QAPISchemaObjectType'],
                          members: List['QAPISchemaObjectTypeMember'],
                          variants: Optional['QAPISchemaVariants']) -> None:
        pass

    def visit_object_type_flat(self,
                               name: str,
                               info: Optional[QAPISourceInfo],
                               ifcond: List[str],
                               features: List['QAPISchemaFeature'],
                               members: List['QAPISchemaObjectTypeMember'],
                               variants: Optional['QAPISchemaVariants'],
                               ) -> None:
        pass

    def visit_alternate_type(self,
                             name: str,
                             info: QAPISourceInfo,
                             ifcond: List[str],
                             features: List['QAPISchemaFeature'],
                             variants: 'QAPISchemaVariants') -> None:
        pass

    def visit_command(self,
                      name: str,
                      info: QAPISourceInfo,
                      ifcond: List[str],
                      features: List['QAPISchemaFeature'],
                      arg_type: 'QAPISchemaObjectType',
                      ret_type: Optional['QAPISchemaType'],
                      gen: bool,
                      success_response: bool,
                      boxed: bool,
                      allow_oob: bool,
                      allow_preconfig: bool,
                      coroutine: bool) -> None:
        pass

    def visit_event(self,
                    name: str,
                    info: QAPISourceInfo,
                    ifcond: List[str],
                    features: List['QAPISchemaFeature'],
                    arg_type: 'QAPISchemaObjectType',
                    boxed: bool) -> None:
        pass


class QAPISchemaModule(Visitable):
    def __init__(self, name: Optional[str]):
        self.name = name
        self._entity_list: List[QAPISchemaEntity] = []

    def add_entity(self, ent: QAPISchemaEntity) -> None:
        self._entity_list.append(ent)

    def visit(self, visitor: QAPISchemaVisitor) -> None:
        visitor.visit_module(self.name)
        for entity in self._entity_list:
            if visitor.visit_needed(entity):
                entity.visit(visitor)


class QAPISchemaInclude(QAPISchemaEntity):
    def __init__(self, sub_module: QAPISchemaModule, info: QAPISourceInfo):
        super().__init__(None, info, None)
        self._sub_module = sub_module

    def visit(self, visitor: QAPISchemaVisitor) -> None:
        super().visit(visitor)
        visitor.visit_include(self._sub_module.name, self.info)


class QAPISchemaType(QAPISchemaEntity):
    # Return the C type for common use.
    # For the types we commonly box, this is a pointer type.
    def c_type(self) -> str:
        raise NotImplementedError()

    # Return the C type to be used in a parameter list.
    def c_param_type(self) -> str:
        return self.c_type()

    # Return the C type to be used where we suppress boxing.
    def c_unboxed_type(self) -> str:
        return self.c_type()

    def json_type(self) -> str:
        raise NotImplementedError()

    def alternate_qtype(self) -> str:
        json2qtype = {
            'null':    'QTYPE_QNULL',
            'string':  'QTYPE_QSTRING',
            'number':  'QTYPE_QNUM',
            'int':     'QTYPE_QNUM',
            'boolean': 'QTYPE_QBOOL',
            'object':  'QTYPE_QDICT'
        }
        return json2qtype[self.json_type()]

    def doc_type(self) -> Optional[str]:
        if self.is_implicit():
            return None
        return self.name

    def check(self, schema: 'QAPISchema') -> None:
        QAPISchemaEntity.check(self, schema)
        if 'deprecated' in [f.name for f in self.features]:
            raise QAPISemError(
                self.info, "feature 'deprecated' is not supported for types")

    def describe(self) -> str:
        assert self.meta
        return "%s type '%s'" % (self.meta, self.name)


class QAPISchemaBuiltinType(QAPISchemaType):
    def __init__(self, name: str, json_type: str, c_type: str):
        super().__init__(name, None, None)
        assert not c_type or isinstance(c_type, str)
        assert json_type in ('string', 'number', 'int', 'boolean', 'null',
                             'value')
        self._json_type_name = json_type
        self._c_type_name = c_type
        self._meta = 'built-in'

    def c_name(self) -> str:
        return self.name

    def c_type(self) -> str:
        return self._c_type_name

    def c_param_type(self) -> str:
        if self.name == 'str':
            return 'const ' + self._c_type_name
        return self._c_type_name

    def json_type(self) -> str:
        return self._json_type_name

    def doc_type(self) -> str:
        return self.json_type()

    def visit(self, visitor: QAPISchemaVisitor) -> None:
        super().visit(visitor)
        visitor.visit_builtin_type(self.name, self.info, self.json_type())


class QAPISchemaEnumType(QAPISchemaType):
    def __init__(self,
                 name: str,
                 info: Optional[QAPISourceInfo],
                 doc: Optional[QAPIDoc],
                 ifcond: Optional[List[str]],
                 features: Optional[List['QAPISchemaFeature']],
                 members: List['QAPISchemaEnumMember'],
                 prefix: Optional[str]):
        super().__init__(name, info, doc, ifcond, features)
        for member in members:
            assert isinstance(member, QAPISchemaEnumMember)
            member.set_defined_in(name)
        assert prefix is None or isinstance(prefix, str)
        self.members = members
        self.prefix = prefix
        self._meta = 'enum'

    def check(self, schema: 'QAPISchema') -> None:
        super().check(schema)
        seen: Dict[str, 'QAPISchemaMember'] = {}
        for member in self.members:
            member.check_clash(self.info, seen)

    def connect_doc(self, doc: Optional[QAPIDoc] = None) -> None:
        super().connect_doc(doc)
        doc = doc or self.doc
        for member in self.members:
            member.connect_doc(doc)

    def is_implicit(self) -> bool:
        # See QAPISchema._make_implicit_enum_type() and ._def_predefineds()
        return self.name.endswith('Kind') or self.name == 'QType'

    def c_type(self) -> str:
        return c_name(self.name)

    def member_names(self) -> List[str]:
        return [m.name for m in self.members]

    def json_type(self) -> str:
        return 'string'

    def visit(self, visitor: QAPISchemaVisitor) -> None:
        super().visit(visitor)
        visitor.visit_enum_type(
            self.name, self.info, self.ifcond, self.features,
            self.members, self.prefix)


class QAPISchemaArrayType(QAPISchemaType):
    def __init__(self, name: str,
                 info: Optional[QAPISourceInfo],
                 element_type: str):
        super().__init__(name, info, None)
        assert isinstance(element_type, str)
        self._element_type_name = element_type
        self.element_type: Optional[QAPISchemaType] = None
        self._meta = 'array'

    def check(self, schema: 'QAPISchema') -> None:
        super().check(schema)
        self.element_type = schema.resolve_type(
            self._element_type_name, self.info,
            self.info.defn_meta if self.info else None)
        assert not isinstance(self.element_type, QAPISchemaArrayType)

    def set_module(self, schema: 'QAPISchema') -> None:
        self._set_module(schema, self.element_type.info)

    @property
    def ifcond(self) -> List[str]:
        assert self._checked
        return self.element_type.ifcond

    def is_implicit(self) -> bool:
        return True

    def c_type(self) -> str:
        return c_name(self.name) + POINTER_SUFFIX

    def json_type(self) -> str:
        return 'array'

    def doc_type(self) -> Optional[str]:
        elt_doc_type = self.element_type.doc_type()
        if not elt_doc_type:
            return None
        return 'array of ' + elt_doc_type

    def visit(self, visitor: QAPISchemaVisitor) -> None:
        super().visit(visitor)
        visitor.visit_array_type(self.name, self.info, self.ifcond,
                                 self.element_type)

    def describe(self) -> str:
        assert self.meta
        return "%s type ['%s']" % (self.meta, self._element_type_name)


class QAPISchemaObjectType(QAPISchemaType):
    def __init__(self,
                 name: str,
                 info: Optional[QAPISourceInfo],
                 doc: Optional[QAPIDoc],
                 ifcond: Optional['QAPISchemaType'],
                 features: Optional[List['QAPISchemaFeature']],
                 base: Optional[str],
                 local_members: List['QAPISchemaObjectTypeMember'],
                 variants: Optional['QAPISchemaVariants']):
        # struct has local_members, optional base, and no variants
        # flat union has base, variants, and no local_members
        # simple union has local_members, variants, and no base
        super().__init__(name, info, doc, ifcond, features)
        self._meta = 'union' if variants else 'struct'
        assert base is None or isinstance(base, str)
        for member in local_members:
            assert isinstance(member, QAPISchemaObjectTypeMember)
            member.set_defined_in(name)
        if variants is not None:
            assert isinstance(variants, QAPISchemaVariants)
            variants.set_defined_in(name)
        self._base_name = base
        self.base: Optional[QAPISchemaObjectType] = None
        self.local_members = local_members
        self.variants = variants
        self.members: Optional[List[QAPISchemaObjectTypeMember]] = None

    def check(self, schema: 'QAPISchema') -> None:
        # This calls another type T's .check() exactly when the C
        # struct emitted by gen_object() contains that T's C struct
        # (pointers don't count).
        if self.members is not None:
            # A previous .check() completed: nothing to do
            return
        if self._checked:
            # Recursed: C struct contains itself
            raise QAPISemError(self.info,
                               "object %s contains itself" % self.name)

        super().check(schema)
        assert self._checked and self.members is None

        seen: Dict[str, 'QAPISchemaMember'] = OrderedDict()
        if self._base_name:
            base = schema.resolve_type(self._base_name, self.info, "'base'")
            if (not isinstance(base, QAPISchemaObjectType)
                    or base.variants):
                raise QAPISemError(
                    self.info,
                    "'base' requires a struct type, %s isn't"
                    % base.describe())
            self.base = base
            self.base.check(schema)
            self.base.check_clash(self.info, seen)
        for member in self.local_members:
            member.check(schema)
            member.check_clash(self.info, seen)

        # check_clash is abstract, but local_members is asserted to be
        # Sequence[QAPISchemaObjectTypeMember]. Cast to the narrower type.
        members = cast(List[QAPISchemaObjectTypeMember], list(seen.values()))

        if self.variants:
            self.variants.check(schema, seen)
            self.variants.check_clash(self.info, seen)

        self.members = members  # mark completed

    # Check that the members of this type do not cause duplicate JSON members,
    # and update seen to track the members seen so far. Report any errors
    # on behalf of info, which is not necessarily self.info
    def check_clash(self,
                    info: QAPISourceInfo,
                    seen: Dict[str, 'QAPISchemaMember']) -> None:
        assert self._checked
        assert not self.variants       # not implemented
        for member in self.members:
            member.check_clash(info, seen)

    def connect_doc(self, doc: Optional[QAPIDoc] = None) -> None:
        super().connect_doc(doc)
        doc = doc or self.doc
        if self.base and self.base.is_implicit():
            self.base.connect_doc(doc)
        for member in self.local_members:
            member.connect_doc(doc)

    @property
    def ifcond(self) -> List[str]:
        assert self._checked
        if isinstance(self._ifcond, QAPISchemaType):
            # Simple union wrapper type inherits from wrapped type;
            # see _make_implicit_object_type()
            return self._ifcond.ifcond
        return self._ifcond

    def is_implicit(self) -> bool:
        # See QAPISchema._make_implicit_object_type(), as well as
        # _def_predefineds()
        return self.name.startswith('q_')

    def is_empty(self) -> bool:
        assert self.members is not None
        return not self.members and not self.variants

    def c_name(self) -> str:
        assert self.name != 'q_empty'
        return super().c_name()

    def c_type(self) -> str:
        assert not self.is_implicit()
        return c_name(self.name) + POINTER_SUFFIX

    def c_unboxed_type(self) -> str:
        return c_name(self.name)

    def json_type(self) -> str:
        return 'object'

    def visit(self, visitor: QAPISchemaVisitor) -> None:
        super().visit(visitor)
        visitor.visit_object_type(
            self.name, self.info, self.ifcond, self.features,
            self.base, self.local_members, self.variants)
        visitor.visit_object_type_flat(
            self.name, self.info, self.ifcond, self.features,
            self.members, self.variants)


class QAPISchemaAlternateType(QAPISchemaType):
    def __init__(self,
                 name: str,
                 info: QAPISourceInfo,
                 doc: QAPIDoc,
                 ifcond: Optional[List[str]],
                 features: List['QAPISchemaFeature'],
                 variants: 'QAPISchemaVariants'):
        super().__init__(name, info, doc, ifcond, features)
        assert isinstance(variants, QAPISchemaVariants)
        assert variants.tag_member
        variants.set_defined_in(name)
        variants.tag_member.set_defined_in(self.name)
        self.variants = variants
        self._meta = 'alternate'

    def check(self, schema: 'QAPISchema') -> None:
        super().check(schema)
        self.variants.tag_member.check(schema)
        # Not calling self.variants.check_clash(), because there's nothing
        # to clash with
        self.variants.check(schema, {})
        # Alternate branch names have no relation to the tag enum values;
        # so we have to check for potential name collisions ourselves.
        seen: Dict[str, QAPISchemaMember] = {}
        types_seen: Dict[str, str] = {}

        for variant in self.variants.variants:
            variant.check_clash(self.info, seen)

            try:
                qtype = variant.type.alternate_qtype()
            except KeyError:
                msg = "{} cannot use {}".format(
                    variant.describe(self.info), variant.type.describe())
                raise QAPISemError(self.info, msg) from None

            conflicting = set([qtype])
            if qtype == 'QTYPE_QSTRING':
                if isinstance(variant.type, QAPISchemaEnumType):
                    for member in variant.type.members:
                        if member.name in ['on', 'off']:
                            conflicting.add('QTYPE_QBOOL')
                        if re.match(r'[-+0-9.]', member.name):
                            # lazy, could be tightened
                            conflicting.add('QTYPE_QNUM')
                else:
                    conflicting.add('QTYPE_QNUM')
                    conflicting.add('QTYPE_QBOOL')

            for qtype in conflicting:
                if qtype in types_seen:
                    msg = "{} can't be distinguished from '{}'".format(
                        variant.describe(self.info), types_seen[qtype])
                    raise QAPISemError(self.info, msg)

                types_seen[qtype] = variant.name

    def connect_doc(self, doc: Optional[QAPIDoc] = None) -> None:
        super().connect_doc(doc)
        doc = doc or self.doc
        for variant in self.variants.variants:
            variant.connect_doc(doc)

    def c_type(self) -> str:
        return c_name(self.name) + POINTER_SUFFIX

    def json_type(self) -> str:
        return 'value'

    def visit(self, visitor: QAPISchemaVisitor) -> None:
        super().visit(visitor)
        visitor.visit_alternate_type(
            self.name, self.info, self.ifcond, self.features, self.variants)


class QAPISchemaVariants:
    def __init__(self,
                 tag_name: Optional[str],
                 info: QAPISourceInfo,
                 tag_member: Optional['QAPISchemaObjectTypeMember'],
                 variants: List['QAPISchemaVariant']):
        # Flat unions pass tag_name but not tag_member.
        # Simple unions and alternates pass tag_member but not tag_name.
        # After check(), tag_member is always set, and tag_name remains
        # a reliable witness of being used by a flat union.
        assert bool(tag_member) != bool(tag_name)
        assert (isinstance(tag_name, str) or
                isinstance(tag_member, QAPISchemaObjectTypeMember))
        for variant in variants:
            assert isinstance(variant, QAPISchemaVariant)
        self._tag_name = tag_name
        self.info = info
        self.tag_member = tag_member
        self.variants = variants

    def set_defined_in(self, name: str) -> None:
        for variant in self.variants:
            variant.set_defined_in(name)

    def check(self,
              schema: 'QAPISchema',
              seen: Dict[str, 'QAPISchemaMember']) -> None:
        if not self.tag_member:  # flat union
            tag_member = seen.get(c_name(self._tag_name))
            base = "'base'"
            # Pointing to the base type when not implicit would be
            # nice, but we don't know it here
            if not tag_member or self._tag_name != tag_member.name:
                raise QAPISemError(
                    self.info,
                    "discriminator '%s' is not a member of %s"
                    % (self._tag_name, base))

            assert isinstance(tag_member, QAPISchemaObjectTypeMember)
            self.tag_member = tag_member
            # Here we do:
            base_type = schema.lookup_type(self.tag_member.defined_in)
            assert base_type
            if not base_type.is_implicit():
                base = "base type '%s'" % self.tag_member.defined_in
            if not isinstance(self.tag_member.type, QAPISchemaEnumType):
                raise QAPISemError(
                    self.info,
                    "discriminator member '%s' of %s must be of enum type"
                    % (self._tag_name, base))
            if self.tag_member.optional:
                raise QAPISemError(
                    self.info,
                    "discriminator member '%s' of %s must not be optional"
                    % (self._tag_name, base))
            if self.tag_member.ifcond:
                raise QAPISemError(
                    self.info,
                    "discriminator member '%s' of %s must not be conditional"
                    % (self._tag_name, base))
        else:                   # simple union
            assert isinstance(self.tag_member.type, QAPISchemaEnumType)
            assert not self.tag_member.optional
            assert self.tag_member.ifcond == []
        if self._tag_name:    # flat union
            # branches that are not explicitly covered get an empty type
            cases = {v.name for v in self.variants}
            for member in self.tag_member.type.members:
                if member.name not in cases:
                    variant = QAPISchemaVariant(member.name, self.info,
                                                'q_empty', member.ifcond)
                    variant.set_defined_in(self.tag_member.defined_in)
                    self.variants.append(variant)
        if not self.variants:
            raise QAPISemError(self.info, "union has no branches")
        for variant in self.variants:
            variant.check(schema)
            # Union names must match enum values; alternate names are
            # checked separately. Use 'seen' to tell the two apart.
            if seen:
                if variant.name not in self.tag_member.type.member_names():
                    raise QAPISemError(
                        self.info,
                        "branch '%s' is not a value of %s"
                        % (variant.name, self.tag_member.type.describe()))
                if (not isinstance(variant.type, QAPISchemaObjectType)
                        or variant.type.variants):
                    raise QAPISemError(
                        self.info,
                        "%s cannot use %s" % (
                            variant.describe(self.info),
                            variant.type.describe()))
                variant.type.check(schema)

    def check_clash(self,
                    info: QAPISourceInfo,
                    seen: Dict[str, 'QAPISchemaMember']) -> None:
        for variant in self.variants:
            # Reset seen map for each variant, since qapi names from one
            # branch do not affect another branch
            assert isinstance(variant.type, QAPISchemaObjectType)
            variant.type.check_clash(info, dict(seen))


class QAPISchemaMember:
    """ Represents object members, enum members and features """
    role = 'member'

    def __init__(self, name: str,
                 info: Optional[QAPISourceInfo],
                 ifcond: Optional[List[str]] = None):
        assert isinstance(name, str)
        self.name = name
        self.info = info
        self.ifcond = ifcond or []
        self.defined_in: Optional[str] = None

    def set_defined_in(self, name: str) -> None:
        assert not self.defined_in
        self.defined_in = name

    def check_clash(self,
                    info: Optional[QAPISourceInfo],
                    seen: Dict[str, 'QAPISchemaMember']) -> None:
        cname = c_name(self.name)
        if cname in seen:
            raise QAPISemError(
                info,
                "%s collides with %s"
                % (self.describe(info), seen[cname].describe(info)))
        seen[cname] = self

    def connect_doc(self, doc: Optional[QAPIDoc]) -> None:
        if doc:
            doc.connect_member(self)

    def describe(self, info: QAPISourceInfo) -> str:
        role = self.role
        defined_in = self.defined_in
        assert defined_in

        if defined_in.startswith('q_obj_'):
            # See QAPISchema._make_implicit_object_type() - reverse the
            # mapping there to create a nice human-readable description
            defined_in = defined_in[6:]
            if defined_in.endswith('-arg'):
                # Implicit type created for a command's dict 'data'
                assert role == 'member'
                role = 'parameter'
            elif defined_in.endswith('-base'):
                # Implicit type created for a flat union's dict 'base'
                role = 'base ' + role
            else:
                # Implicit type created for a simple union's branch
                assert defined_in.endswith('-wrapper')
                # Unreachable and not implemented
                assert False
        elif defined_in.endswith('Kind'):
            # See QAPISchema._make_implicit_enum_type()
            # Implicit enum created for simple union's branches
            assert role == 'value'
            role = 'branch'
        elif defined_in != info.defn_name:
            return "%s '%s' of type '%s'" % (role, self.name, defined_in)
        return "%s '%s'" % (role, self.name)


class QAPISchemaEnumMember(QAPISchemaMember):
    role = 'value'


class QAPISchemaFeature(QAPISchemaMember):
    role = 'feature'


class QAPISchemaObjectTypeMember(QAPISchemaMember):
    def __init__(self,
                 name: str,
                 info: QAPISourceInfo,
                 typ: str,
                 optional: bool,
                 ifcond: Optional[List[str]] = None,
                 features: Optional[List[QAPISchemaFeature]] = None):
        super().__init__(name, info, ifcond)
        assert isinstance(typ, str)
        assert isinstance(optional, bool)
        for feature in features or []:
            assert isinstance(feature, QAPISchemaFeature)
            feature.set_defined_in(name)
        self._type_name = typ
        self.type: Optional[QAPISchemaType] = None
        self.optional = optional
        self.features = features or []

    def check(self, schema: 'QAPISchema') -> None:
        assert self.defined_in
        self.type = schema.resolve_type(self._type_name, self.info,
                                        self.describe)
        seen: Dict[str, QAPISchemaMember] = {}
        for feature in self.features:
            feature.check_clash(self.info, seen)

    def connect_doc(self, doc: Optional[QAPIDoc]) -> None:
        super().connect_doc(doc)
        if doc:
            for feature in self.features:
                doc.connect_feature(feature)


class QAPISchemaVariant(QAPISchemaObjectTypeMember):
    role = 'branch'

    def __init__(self,
                 name: str,
                 info: QAPISourceInfo,
                 typ: str,
                 ifcond: Optional[List[str]] = None):
        super().__init__(name, info, typ, False, ifcond)


class QAPISchemaCommand(QAPISchemaEntity):
    def __init__(self,
                 name: str,
                 info: QAPISourceInfo,
                 doc: QAPIDoc,
                 ifcond: Optional[List[str]],
                 features: List[QAPISchemaFeature],
                 arg_type: str,
                 ret_type: Optional[str],
                 gen: bool,
                 success_response: bool,
                 boxed: bool,
                 allow_oob: bool,
                 allow_preconfig: bool,
                 coroutine: bool):
        super().__init__(name, info, doc, ifcond, features)
        assert not arg_type or isinstance(arg_type, str)
        assert not ret_type or isinstance(ret_type, str)
        self._arg_type_name = arg_type
        self.arg_type: Optional[QAPISchemaObjectType] = None
        self._ret_type_name = ret_type
        self.ret_type: Optional[QAPISchemaType] = None
        self.gen = gen
        self.success_response = success_response
        self.boxed = boxed
        self.allow_oob = allow_oob
        self.allow_preconfig = allow_preconfig
        self.coroutine = coroutine
        self._meta = 'command'

    def check(self, schema: 'QAPISchema') -> None:
        super().check(schema)
        if self._arg_type_name:
            arg_type = schema.resolve_type(
                self._arg_type_name, self.info, "command's 'data'")
            if not isinstance(arg_type, QAPISchemaObjectType):
                raise QAPISemError(
                    self.info,
                    "command's 'data' cannot take %s"
                    % arg_type.describe())
            self.arg_type = arg_type
            if self.arg_type.variants and not self.boxed:
                raise QAPISemError(
                    self.info,
                    "command's 'data' can take %s only with 'boxed': true"
                    % self.arg_type.describe())
        if self._ret_type_name:
            self.ret_type = schema.resolve_type(
                self._ret_type_name, self.info, "command's 'returns'")
            if self.name not in self.info.pragma.returns_whitelist:
                typ = self.ret_type
                if isinstance(self.ret_type, QAPISchemaArrayType):
                    typ = self.ret_type.element_type
                    assert typ
                if not isinstance(typ, QAPISchemaObjectType):
                    raise QAPISemError(
                        self.info,
                        "command's 'returns' cannot take %s"
                        % self.ret_type.describe())

    def connect_doc(self, doc: Optional[QAPIDoc] = None) -> None:
        super().connect_doc(doc)
        doc = doc or self.doc
        if doc:
            if self.arg_type and self.arg_type.is_implicit():
                self.arg_type.connect_doc(doc)

    def visit(self, visitor: QAPISchemaVisitor) -> None:
        super().visit(visitor)
        visitor.visit_command(
            self.name, self.info, self.ifcond, self.features,
            self.arg_type, self.ret_type, self.gen, self.success_response,
            self.boxed, self.allow_oob, self.allow_preconfig,
            self.coroutine)


class QAPISchemaEvent(QAPISchemaEntity):
    def __init__(self,
                 name: str,
                 info: QAPISourceInfo,
                 doc: QAPIDoc,
                 ifcond: Optional[List[str]],
                 features: List[QAPISchemaFeature],
                 arg_type: str,
                 boxed: bool):
        super().__init__(name, info, doc, ifcond, features)
        assert not arg_type or isinstance(arg_type, str)
        self._arg_type_name = arg_type
        self.arg_type: Optional[QAPISchemaObjectType] = None
        self.boxed = boxed
        self._meta = 'event'

    def check(self, schema: 'QAPISchema') -> None:
        super().check(schema)
        if self._arg_type_name:
            arg_type = schema.resolve_type(
                self._arg_type_name, self.info, "event's 'data'")
            if not isinstance(arg_type, QAPISchemaObjectType):
                raise QAPISemError(
                    self.info,
                    "event's 'data' cannot take %s"
                    % arg_type.describe())
            self.arg_type = arg_type
            if self.arg_type.variants and not self.boxed:
                raise QAPISemError(
                    self.info,
                    "event's 'data' can take %s only with 'boxed': true"
                    % self.arg_type.describe())

    def connect_doc(self, doc: Optional[QAPIDoc] = None) -> None:
        super().connect_doc(doc)
        doc = doc or self.doc
        if doc:
            if self.arg_type and self.arg_type.is_implicit():
                self.arg_type.connect_doc(doc)

    def visit(self, visitor: QAPISchemaVisitor) -> None:
        super().visit(visitor)
        visitor.visit_event(
            self.name, self.info, self.ifcond, self.features,
            self.arg_type, self.boxed)


_EntityType = TypeVar('_EntityType', bound=QAPISchemaEntity)


class QAPISchema(Visitable):
    def __init__(self, fname: str):
        self.fname = fname
        parser = QAPISchemaParser(fname)
        exprs = check_exprs(parser.exprs)
        self.docs = parser.docs
        self._entity_list: List[QAPISchemaEntity] = []
        self._entity_dict: Dict[str, QAPISchemaEntity] = {}
        self._module_dict: Dict[str, QAPISchemaModule] = OrderedDict()
        self._schema_dir = os.path.dirname(fname)
        self._make_module(None)  # built-ins
        self._make_module(fname)
        self._predefining = True
        self._def_predefineds()
        self._predefining = False
        self._def_exprs(exprs)
        self.check()

    def _def_entity(self, ent: QAPISchemaEntity) -> None:
        # Only the predefined types are allowed to not have info
        assert ent.info or self._predefining
        self._entity_list.append(ent)
        if ent.name is None:
            return
        # TODO reject names that differ only in '_' vs. '.'  vs. '-',
        # because they're liable to clash in generated C.
        other_ent = self._entity_dict.get(ent.name)
        if other_ent:
            if other_ent.info:
                where = QAPISourceError(other_ent.info, "previous definition")
                raise QAPISemError(
                    ent.info,
                    "'%s' is already defined\n%s" % (ent.name, where))
            raise QAPISemError(
                ent.info, "%s is already defined" % other_ent.describe())
        self._entity_dict[ent.name] = ent

    @overload
    def lookup_entity(self, name: str,
                      typ: None = None) -> Optional[QAPISchemaEntity]: ...

    @overload
    def lookup_entity(self, name: str,
                      typ: Type[_EntityType]) -> Optional[_EntityType]: ...

    def lookup_entity(self,
                      name: str,
                      typ: Optional[Type[QAPISchemaEntity]] = None,
                      ) -> Optional[QAPISchemaEntity]:
        ent = self._entity_dict.get(name)
        if typ and not isinstance(ent, typ):
            return None
        return ent

    def lookup_type(self, name: str) -> QAPISchemaType:
        return self.lookup_entity(name, QAPISchemaType)

    def resolve_type(self,
                     name: str,
                     info: Optional[QAPISourceInfo],
                     what: Optional[
                         Union[str, Callable[[Optional[QAPISourceInfo]], str]]
                     ],
                     ) -> QAPISchemaType:
        typ = self.lookup_type(name)
        if not typ:
            if callable(what):
                what = what(info)
            raise QAPISemError(
                info, "%s uses unknown type '%s'" % (what, name))
        return typ

    def _module_name(self, fname: Optional[str]) -> Optional[str]:
        if fname is None:
            return None
        return os.path.relpath(fname, self._schema_dir)

    def _make_module(self, fname: Optional[str]) -> QAPISchemaModule:
        name = self._module_name(fname)
        if name not in self._module_dict:
            self._module_dict[name] = QAPISchemaModule(name)
        return self._module_dict[name]

    def module_by_fname(self, fname: Optional[str]) -> QAPISchemaModule:
        name = self._module_name(fname)
        return self._module_dict[name]

    def _def_include(self,
                     expr: Dict[str, Any],
                     info: QAPISourceInfo,
                     doc: Optional[QAPIDoc]) -> None:
        include = expr['include']
        assert doc is None
        self._def_entity(QAPISchemaInclude(self._make_module(include), info))

    def _def_builtin_type(self,
                          name: str,
                          json_type: str,
                          c_type: str) -> None:
        self._def_entity(QAPISchemaBuiltinType(name, json_type, c_type))
        # Instantiating only the arrays that are actually used would
        # be nice, but we can't as long as their generated code
        # (qapi-builtin-types.[ch]) may be shared by some other
        # schema.
        self._make_array_type(name, None)

    def _def_predefineds(self) -> None:
        for args in (('str',    'string',  'char' + POINTER_SUFFIX),
                     ('number', 'number',  'double'),
                     ('int',    'int',     'int64_t'),
                     ('int8',   'int',     'int8_t'),
                     ('int16',  'int',     'int16_t'),
                     ('int32',  'int',     'int32_t'),
                     ('int64',  'int',     'int64_t'),
                     ('uint8',  'int',     'uint8_t'),
                     ('uint16', 'int',     'uint16_t'),
                     ('uint32', 'int',     'uint32_t'),
                     ('uint64', 'int',     'uint64_t'),
                     ('size',   'int',     'uint64_t'),
                     ('bool',   'boolean', 'bool'),
                     ('any',    'value',   'QObject' + POINTER_SUFFIX),
                     ('null',   'null',    'QNull' + POINTER_SUFFIX)):
            self._def_builtin_type(*args)
        self.the_empty_object_type = QAPISchemaObjectType(
            'q_empty', None, None, None, None, None, [], None)
        self._def_entity(self.the_empty_object_type)

        qtypes = ['none', 'qnull', 'qnum', 'qstring', 'qdict', 'qlist',
                  'qbool']
        qtype_values = self._make_enum_members(
            [{'name': n} for n in qtypes], None)

        self._def_entity(QAPISchemaEnumType('QType', None, None, None, None,
                                            qtype_values, 'QTYPE'))

    @classmethod
    def _make_features(cls,
                       features: Optional[List[Dict[str, Any]]],
                       info: QAPISourceInfo) -> List[QAPISchemaFeature]:
        if features is None:
            return []
        return [QAPISchemaFeature(f['name'], info, f.get('if'))
                for f in features]

    @classmethod
    def _make_enum_members(cls,
                           values: List[Dict[str, Any]],
                           info: Optional[QAPISourceInfo],
                           ) -> List[QAPISchemaEnumMember]:
        return [QAPISchemaEnumMember(v['name'], info, v.get('if'))
                for v in values]

    def _make_implicit_enum_type(self,
                                 name: str,
                                 info: QAPISourceInfo,
                                 ifcond: Optional[List[str]],
                                 values: List[Dict[str, Any]]) -> str:
        # See also QAPISchemaObjectTypeMember.describe()
        name = name + 'Kind'    # reserved by check_defn_name_str()
        self._def_entity(QAPISchemaEnumType(
            name, info, None, ifcond, None,
            self._make_enum_members(values, info),
            None))
        return name

    def _make_array_type(self,
                         element_type: str,
                         info: QAPISourceInfo) -> str:
        name = element_type + 'List'    # reserved by check_defn_name_str()
        if not self.lookup_type(name):
            self._def_entity(QAPISchemaArrayType(name, info, element_type))
        return name

    def _make_implicit_object_type(self,
                                   name: str,
                                   info: QAPISourceInfo,
                                   ifcond: Optional[QAPISchemaType],
                                   role: str,
                                   members: List[QAPISchemaObjectTypeMember],
                                   ) -> Optional[str]:
        if not members:
            return None
        # See also QAPISchemaObjectTypeMember.describe()
        name = 'q_obj_%s-%s' % (name, role)
        typ = self.lookup_entity(name, QAPISchemaObjectType)
        if typ:
            # The implicit object type has multiple users.  This can
            # happen only for simple unions' implicit wrapper types.
            # Its ifcond should be the disjunction of its user's
            # ifconds.  Not implemented.  Instead, we always pass the
            # wrapped type's ifcond, which is trivially the same for all
            # users.  It's also necessary for the wrapper to compile.
            # But it's not tight: the disjunction need not imply it.  We
            # may end up compiling useless wrapper types.
            # TODO kill simple unions or implement the disjunction

            # pylint: disable=protected-access
            assert (ifcond or []) == typ._ifcond
        else:
            self._def_entity(QAPISchemaObjectType(
                name, info, None, ifcond, None, None, members, None))
        return name

    def _def_enum_type(self,
                       expr: Dict[str, Any],
                       info: QAPISourceInfo,
                       doc: QAPIDoc) -> None:
        name = expr['enum']
        data = expr['data']
        prefix = expr.get('prefix')
        ifcond = expr.get('if')
        features = self._make_features(expr.get('features'), info)
        self._def_entity(QAPISchemaEnumType(
            name, info, doc, ifcond, features,
            self._make_enum_members(data, info), prefix))

    def _make_member(self,
                     name: str,
                     typ: str,
                     ifcond: Optional[List[str]],
                     features: Optional[List[Dict[str, Any]]],
                     info: QAPISourceInfo) -> QAPISchemaObjectTypeMember:
        optional = False
        if name.startswith('*'):
            name = name[1:]
            optional = True
        if isinstance(typ, list):
            assert len(typ) == 1
            typ = self._make_array_type(typ[0], info)
        return QAPISchemaObjectTypeMember(name, info, typ, optional, ifcond,
                                          self._make_features(features, info))

    def _make_members(self,
                      data: Dict[str, Dict[str, Any]],
                      info: QAPISourceInfo,
                      ) -> List[QAPISchemaObjectTypeMember]:
        return [self._make_member(key, value['type'], value.get('if'),
                                  value.get('features'), info)
                for (key, value) in data.items()]

    def _def_struct_type(self,
                         expr: Dict[str, Any],
                         info: QAPISourceInfo,
                         doc: QAPIDoc) -> None:
        name = expr['struct']
        base = expr.get('base')
        data = expr['data']
        ifcond = expr.get('if')
        features = self._make_features(expr.get('features'), info)
        self._def_entity(QAPISchemaObjectType(
            name, info, doc, ifcond, features, base,
            self._make_members(data, info),
            None))

    @classmethod
    def _make_variant(cls,
                      case: str,
                      typ: str,
                      ifcond: Optional[List[str]],
                      info: QAPISourceInfo) -> QAPISchemaVariant:
        return QAPISchemaVariant(case, info, typ, ifcond)

    def _make_simple_variant(self,
                             case: str,
                             typ: str,
                             ifcond: Optional[List[str]],
                             info: QAPISourceInfo) -> QAPISchemaVariant:
        if isinstance(typ, list):
            assert len(typ) == 1
            typ = self._make_array_type(typ[0], info)
        typ = self._make_implicit_object_type(
            typ, info, self.lookup_type(typ),
            'wrapper', [self._make_member('data', typ, None, None, info)])
        return QAPISchemaVariant(case, info, typ, ifcond)

    def _def_union_type(self,
                        expr: Dict[str, Any],
                        info: QAPISourceInfo,
                        doc: QAPIDoc) -> None:
        name = expr['union']
        data = expr['data']
        base = expr.get('base')
        ifcond = expr.get('if')
        features = self._make_features(expr.get('features'), info)
        tag_name = expr.get('discriminator')
        tag_member = None
        if isinstance(base, dict):
            base = self._make_implicit_object_type(
                name, info, ifcond,
                'base', self._make_members(base, info))
        if tag_name:
            variants = [self._make_variant(key, value['type'],
                                           value.get('if'), info)
                        for (key, value) in data.items()]
            members = []
        else:
            variants = [self._make_simple_variant(key, value['type'],
                                                  value.get('if'), info)
                        for (key, value) in data.items()]
            enum = [{'name': v.name, 'if': v.ifcond} for v in variants]
            typ = self._make_implicit_enum_type(name, info, ifcond, enum)
            tag_member = QAPISchemaObjectTypeMember('type', info, typ, False)
            members = [tag_member]
        self._def_entity(
            QAPISchemaObjectType(name, info, doc, ifcond, features,
                                 base, members,
                                 QAPISchemaVariants(
                                     tag_name, info, tag_member, variants)))

    def _def_alternate_type(self,
                            expr: Dict[str, Any],
                            info: QAPISourceInfo,
                            doc: QAPIDoc) -> None:
        name = expr['alternate']
        data = expr['data']
        ifcond = expr.get('if')
        features = self._make_features(expr.get('features'), info)
        variants = [self._make_variant(key, value['type'], value.get('if'),
                                       info)
                    for (key, value) in data.items()]
        tag_member = QAPISchemaObjectTypeMember('type', info, 'QType', False)
        self._def_entity(
            QAPISchemaAlternateType(name, info, doc, ifcond, features,
                                    QAPISchemaVariants(
                                        None, info, tag_member, variants)))

    def _def_command(self,
                     expr: Dict[str, Any],
                     info: QAPISourceInfo,
                     doc: QAPIDoc) -> None:
        name = expr['command']
        data = expr.get('data')
        rets = expr.get('returns')
        gen = expr.get('gen', True)
        success_response = expr.get('success-response', True)
        boxed = expr.get('boxed', False)
        allow_oob = expr.get('allow-oob', False)
        allow_preconfig = expr.get('allow-preconfig', False)
        coroutine = expr.get('coroutine', False)
        ifcond = expr.get('if')
        features = self._make_features(expr.get('features'), info)
        if isinstance(data, OrderedDict):
            data = self._make_implicit_object_type(
                name, info, ifcond,
                'arg', self._make_members(data, info))
        if isinstance(rets, list):
            assert len(rets) == 1
            rets = self._make_array_type(rets[0], info)
        self._def_entity(QAPISchemaCommand(name, info, doc, ifcond, features,
                                           data, rets,
                                           gen, success_response,
                                           boxed, allow_oob, allow_preconfig,
                                           coroutine))

    def _def_event(self,
                   expr: Dict[str, Any],
                   info: QAPISourceInfo,
                   doc: QAPIDoc) -> None:
        name = expr['event']
        data = expr.get('data')
        boxed = expr.get('boxed', False)
        ifcond = expr.get('if')
        features = self._make_features(expr.get('features'), info)
        if isinstance(data, OrderedDict):
            data = self._make_implicit_object_type(
                name, info, ifcond,
                'arg', self._make_members(data, info))
        self._def_entity(QAPISchemaEvent(name, info, doc, ifcond, features,
                                         data, boxed))

    def _def_exprs(self, exprs: List[ParsedExpression]) -> None:
        for expr_elem in exprs:
            expr = expr_elem.expr
            info = expr_elem.info
            doc = expr_elem.doc
            if 'enum' in expr:
                self._def_enum_type(expr, info, doc)
            elif 'struct' in expr:
                self._def_struct_type(expr, info, doc)
            elif 'union' in expr:
                self._def_union_type(expr, info, doc)
            elif 'alternate' in expr:
                self._def_alternate_type(expr, info, doc)
            elif 'command' in expr:
                self._def_command(expr, info, doc)
            elif 'event' in expr:
                self._def_event(expr, info, doc)
            elif 'include' in expr:
                self._def_include(expr, info, doc)
            else:
                assert False

    def check(self) -> None:
        for ent in self._entity_list:
            ent.check(self)
            ent.connect_doc()
            ent.check_doc()
        for ent in self._entity_list:
            ent.set_module(self)

    def visit(self, visitor: QAPISchemaVisitor) -> None:
        visitor.visit_begin(self)
        for mod in self._module_dict.values():
            mod.visit(visitor)
        visitor.visit_end()
