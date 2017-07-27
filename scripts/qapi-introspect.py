#
# QAPI introspection generator
#
# Copyright (C) 2015-2016 Red Hat, Inc.
#
# Authors:
#  Markus Armbruster <armbru@redhat.com>
#
# This work is licensed under the terms of the GNU GPL, version 2.
# See the COPYING file in the top-level directory.

from qapi import *


def to_qlit(obj, level=0, first_indent=True, suffix=''):
    def indent(level):
        return level * 4 * ' '
    ret = ''
    if first_indent:
        ret += indent(level)
    if obj is None:
        ret += 'QLIT_QNULL'
    elif isinstance(obj, tuple):
        obj, ifcond =  obj
        ret += gen_if(ifcond)
        ret += to_qlit(obj, level, False) + suffix
        ret += gen_endif(ifcond)
        suffix = ''
    elif isinstance(obj, str):
        ret += 'QLIT_QSTR(' + '"' + obj.replace('"', r'\"') + '"' + ')'
    elif isinstance(obj, list):
        elts = [to_qlit(elt, level + 1, True, ",")
                for elt in obj]
        elts.append(indent(level + 1) + "{ }")
        ret += 'QLIT_QLIST(((QLitObject[]) {\n'
        ret += '\n'.join(elts) + '\n'
        ret += indent(level) + '}))'
    elif isinstance(obj, dict):
        elts = [ indent(level + 1) + '{ "%s", %s }' %
                 (key.replace('"', r'\"'), to_qlit(obj[key], level + 1, False))
                 for key in sorted(obj.keys())]
        elts.append(indent(level + 1) + '{ }')
        ret += 'QLIT_QDICT(((QLitDictEntry[]) {\n'
        ret += ',\n'.join(elts) + '\n'
        ret += indent(level) + '}))'
    else:
        assert False                # not implemented
    return ret + suffix


class QAPISchemaGenIntrospectVisitor(QAPISchemaVisitor):
    def __init__(self, unmask):
        self._unmask = unmask
        self.defn = None
        self.decl = None
        self._schema = None
        self._qlits = None
        self._used_types = None
        self._name_map = None

    def visit_begin(self, schema):
        self._schema = schema
        self._qlits = []
        self._used_types = []
        self._name_map = {}

    def visit_end(self):
        # visit the types that are actually used
        qlits = self._qlits
        self._qlits = []
        for typ in self._used_types:
            typ.visit(self)
        # generate C
        # TODO can generate awfully long lines
        qlits.extend(self._qlits)
        name = c_name(prefix, protect=False) + 'qmp_schema_qlit'
        self.decl = mcgen('''
extern const QLitObject %(c_name)s;
''',
                          c_name=c_name(name))
        c_string = to_qlit(qlits)
        self.defn = mcgen('''
const QLitObject %(c_name)s = %(c_string)s;
''',
                          c_name=c_name(name),
                          c_string=c_string)
        self._schema = None
        self._qlits = None
        self._used_types = None
        self._name_map = None

    def visit_needed(self, entity):
        # Ignore types on first pass; visit_end() will pick up used types
        return not isinstance(entity, QAPISchemaType)

    def _name(self, name):
        if self._unmask:
            return name
        if name not in self._name_map:
            self._name_map[name] = '%d' % len(self._name_map)
        return self._name_map[name]

    def _use_type(self, typ):
        # Map the various integer types to plain int
        if typ.json_type() == 'int':
            typ = self._schema.lookup_type('int')
        elif (isinstance(typ, QAPISchemaArrayType) and
              typ.element_type.json_type() == 'int'):
            typ = self._schema.lookup_type('intList')
        # Add type to work queue if new
        if typ not in self._used_types:
            self._used_types.append(typ)
        # Clients should examine commands and events, not types.  Hide
        # type names to reduce the temptation.  Also saves a few
        # characters.
        if isinstance(typ, QAPISchemaBuiltinType):
            return typ.name
        if isinstance(typ, QAPISchemaArrayType):
            return '[' + self._use_type(typ.element_type) + ']'
        return self._name(typ.name)

    def _gen_qlit(self, name, mtype, obj, ifcond):
        if mtype not in ('command', 'event', 'builtin', 'array'):
            name = self._name(name)
        obj['name'] = name
        obj['meta-type'] = mtype
        self._qlits.append((obj, ifcond))

    def _gen_member(self, member):
        ret = {'name': member.name, 'type': self._use_type(member.type)}
        if member.optional:
            ret['default'] = None
        if member.ifcond:
            ret = (ret, member.ifcond)
        return ret

    def _gen_variants(self, tag_name, variants):
        return {'tag': tag_name,
                'variants': [self._gen_variant(v) for v in variants]}

    def _gen_variant(self, variant):
        return {'case': variant.name, 'type': self._use_type(variant.type)}

    def visit_builtin_type(self, name, info, json_type):
        self._gen_qlit(name, 'builtin', {'json-type': json_type}, None)

    def visit_enum_type(self, name, info, values, prefix, ifcond):
        self._gen_qlit(name, 'enum', {'values': values}, ifcond)

    def visit_array_type(self, name, info, element_type, ifcond):
        element = self._use_type(element_type)
        self._gen_qlit('[' + element + ']', 'array', {'element-type': element},
                       ifcond)

    def visit_object_type_flat(self, name, info, members, variants, ifcond):
        obj = {'members': [self._gen_member(m) for m in members]}
        if variants:
            obj.update(self._gen_variants(variants.tag_member.name,
                                          variants.variants))
        self._gen_qlit(name, 'object', obj, ifcond)

    def visit_alternate_type(self, name, info, variants, ifcond):
        self._gen_qlit(name, 'alternate',
                       {'members': [{'type': self._use_type(m.type)}
                                    for m in variants.variants]}, ifcond)

    def visit_command(self, name, info, arg_type, ret_type,
                      gen, success_response, boxed, ifcond):
        arg_type = arg_type or self._schema.the_empty_object_type
        ret_type = ret_type or self._schema.the_empty_object_type
        self._gen_qlit(name, 'command',
                       {'arg-type': self._use_type(arg_type),
                        'ret-type': self._use_type(ret_type)}, ifcond)

    def visit_event(self, name, info, arg_type, boxed, ifcond):
        arg_type = arg_type or self._schema.the_empty_object_type
        self._gen_qlit(name, 'event', {'arg-type': self._use_type(arg_type)},
                       ifcond)

# Debugging aid: unmask QAPI schema's type names
# We normally mask them, because they're not QMP wire ABI
opt_unmask = False

(input_file, output_dir, do_c, do_h, prefix, opts) = \
    parse_command_line('u', ['unmask-non-abi-names'])

for o, a in opts:
    if o in ('-u', '--unmask-non-abi-names'):
        opt_unmask = True

c_comment = '''
/*
 * QAPI/QMP schema introspection
 *
 * Copyright (C) 2015 Red Hat, Inc.
 *
 * This work is licensed under the terms of the GNU LGPL, version 2.1 or later.
 * See the COPYING.LIB file in the top-level directory.
 *
 */
'''
h_comment = '''
/*
 * QAPI/QMP schema introspection
 *
 * Copyright (C) 2015 Red Hat, Inc.
 *
 * This work is licensed under the terms of the GNU LGPL, version 2.1 or later.
 * See the COPYING.LIB file in the top-level directory.
 *
 */
'''

(fdef, fdecl) = open_output(output_dir, do_c, do_h, prefix,
                            'qmp-introspect.c', 'qmp-introspect.h',
                            c_comment, h_comment)

fdef.write(mcgen('''
#include "qemu/osdep.h"
#include "qapi/qmp/qlit.h"
#include "%(prefix)sqmp-introspect.h"

''',
                 prefix=prefix))

fdecl.write(mcgen('''
#include "qemu/osdep.h"
#include "qapi/qmp/qlit.h"

'''))

schema = QAPISchema(input_file)
gen = QAPISchemaGenIntrospectVisitor(opt_unmask)
schema.visit(gen)
fdef.write(gen.defn)
fdecl.write(gen.decl)

close_output(fdef, fdecl)
