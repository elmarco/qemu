util_ss.add(files(
  'opts-visitor.c',
  'qapi-clone-visitor.c',
  'qapi-dealloc-visitor.c',
  'qapi-util.c',
  'qapi-visit-core.c',
  'qmp-dispatch.c',
  'qmp-event.c',
  'qmp-registry.c',
  'qobject-input-visitor.c',
  'qobject-output-visitor.c',
  'string-input-visitor.c',
  'string-output-visitor.c',
))

qapi_common_modules = [
  'audio',
  'authz',
  'block-core',
  'block',
  'char',
  'common',
  'crypto',
  'dump',
  'error',
  'introspect',
  'job',
  'machine',
  'migration',
  'misc',
  'net',
  'qdev',
  'qom',
  'rdma',
  'rocker',
  'run-state',
  'sockets',
  'tpm',
  'trace',
  'transaction',
  'ui',
]

qapi_target_modules = [ 'machine-target', 'misc-target' ]

qapi_util_outputs = [
  'qapi-builtin-types.c', 'qapi-builtin-visit.c',
  'qapi-emit-events.c'
]
qapi_all_outputs = qapi_util_outputs
qapi_inputs = []
foreach module : qapi_common_modules + qapi_target_modules
  qapi_module_outputs = [
    'qapi-types-@0@.c'.format(module),
    'qapi-types-@0@.h'.format(module),
    'qapi-visit-@0@.c'.format(module),
    'qapi-visit-@0@.h'.format(module),
    'qapi-commands-@0@.c'.format(module),
    'qapi-commands-@0@.h'.format(module),
    'qapi-events-@0@.c'.format(module),
    'qapi-events-@0@.h'.format(module),
  ]
  qapi_inputs += [ files(module + '.json') ]
  qapi_all_outputs += qapi_module_outputs
  if qapi_common_modules.contains(module)
    qapi_util_outputs += qapi_module_outputs
  endif
endforeach

qapi_specific_outputs = [
  'qapi-introspect.c', 'qapi-introspect.h',
  'qapi-types.c', 'qapi-types.h',
  'qapi-visit.c', 'qapi-visit.h',
  'qapi-events.c', 'qapi-events.h',
  'qapi-commands.c', 'qapi-commands.h',
]

qapi_all_outputs += qapi_specific_outputs
qapi_all_outputs += 'qapi-doc.texi'

qapi_files = custom_target('QAPI files',
  output: qapi_all_outputs,
  input: [ files('qapi-schema.json') ],
  command: [ qapi_gen, '-o', 'qapi', '-b', '@INPUT0@' ],
  depend_files: [ qapi_inputs, qapi_gen_depends ])

# qapi_util_outputs must be at the beginning of qapi_all_outputs.
i = 0
foreach output : qapi_util_outputs
  util_ss.add(qapi_files[i])
  if qapi_util_outputs[i].endswith('.h')
    genh += qapi_files[i]
  endif
  i = i + 1
endforeach

i = 0
foreach output : qapi_all_outputs
  if output in qapi_specific_outputs
    specific_ss.add(when: 'CONFIG_SOFTMMU', if_true: qapi_files[i])
  endif
  if output.endswith('-target.c')
    specific_ss.add(when: 'CONFIG_SOFTMMU', if_true: qapi_files[i])
  endif
  i = i + 1
endforeach
