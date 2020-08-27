py3 = import('python').find_installation()

qht_bench = executable('qht-bench',
                       sources: files('qht-bench.c'),
                       dependencies: [qemuutil])

test_qapi_outputs = [
  'qapi-builtin-types.c',
  'qapi-builtin-types.h',
  'qapi-builtin-visit.c',
  'qapi-builtin-visit.h',
  'test-qapi-commands-sub-sub-module.c',
  'test-qapi-commands-sub-sub-module.h',
  'test-qapi-commands.c',
  'test-qapi-commands.h',
  'test-qapi-emit-events.c',
  'test-qapi-emit-events.h',
  'test-qapi-events-sub-sub-module.c',
  'test-qapi-events-sub-sub-module.h',
  'test-qapi-events.c',
  'test-qapi-events.h',
  'test-qapi-init-commands.c',
  'test-qapi-init-commands.h',
  'test-qapi-introspect.c',
  'test-qapi-introspect.h',
  'test-qapi-types-sub-sub-module.c',
  'test-qapi-types-sub-sub-module.h',
  'test-qapi-types.c',
  'test-qapi-types.h',
  'test-qapi-visit-sub-sub-module.c',
  'test-qapi-visit-sub-sub-module.h',
  'test-qapi-visit.c',
  'test-qapi-visit.h',
]

# meson doesn't like generated output in other directories:
subdir('include')

test_qapi_files = custom_target('Test QAPI files',
                                output: test_qapi_outputs,
                                input: files('qapi-schema/qapi-schema-test.json',
                                             'qapi-schema/include/sub-module.json',
                                             'qapi-schema/sub-sub-module.json'),
                                command: [ qapi_gen, '-o', meson.current_build_dir(),
                                           '-b', '-p', 'test-', '@INPUT0@' ],
                                depend_files: qapi_gen_depends)

libtestqapi = static_library('testqapi', sources: [test_qapi_files, test_qapi_outputs_extra])
testqapi = declare_dependency(link_with: libtestqapi)

testblock = declare_dependency(dependencies: [block], sources: files('iothread.c'))

tests = {
  'check-block-qdict': {},
  'check-qdict': {},
  'check-qnum': {},
  'check-qstring': {},
  'check-qlist': {},
  'check-qnull': {},
  'check-qobject': {},
  'check-qjson': {},
  'check-qlit': {},
  'test-qobject-output-visitor': {'deps': [testqapi]},
  'test-clone-visitor': {'deps': [testqapi]},
  'test-qobject-input-visitor': {'deps': [testqapi]},
  'test-string-input-visitor': {'deps': [testqapi]},
  'test-string-output-visitor': {'deps': [testqapi]},
  'test-qmp-event': {'deps': [testqapi]},
  'test-opts-visitor': {'deps': [testqapi]},
  'test-visitor-serialization': {'deps': [testqapi]},
  'test-bitmap': {},
  # all code tested by test-x86-cpuid is inside topology.h
  'test-x86-cpuid': {},
  'test-cutils': {},
  'test-shift128': {},
  'test-mul64': {},
  # all code tested by test-int128 is inside int128.h
  'test-int128': {},
  'rcutorture': {},
  'test-rcu-list': {},
  'test-rcu-simpleq': {},
  'test-rcu-tailq': {},
  'test-rcu-slist': {},
  'test-qdist': {},
  'test-qht': {},
  'test-qht-par': {'test_deps': [qht_bench]},
  'test-bitops': {},
  'test-bitcnt': {},
  'test-qgraph': {'extra_src': files('qtest/libqos/qgraph.c')},
  'check-qom-interface': {'deps': [qom]},
  'check-qom-proplist': {'deps': [qom]},
  'test-qemu-opts': {},
  'test-keyval': {'deps': [testqapi]},
  'test-logging': {},
  'test-uuid': {},
  'ptimer-test': {
    'extra_src': files('ptimer-test-stubs.c', meson.source_root() / 'hw/core/ptimer.c')},
  'test-qapi-util': {},
}

if have_block
  tests += {
    'test-coroutine': {'deps': [testblock]},
    'test-aio': {'deps': [testblock]},
    'test-aio-multithread': {'deps': [testblock]},
    'test-throttle': {'deps': [testblock]},
    'test-thread-pool': {'deps': [testblock]},
    'test-hbitmap': {'deps': [testblock]},
    'test-bdrv-drain': {'deps': [testblock]},
    'test-bdrv-graph-mod': {'deps': [testblock]},
    'test-blockjob': {'deps': [testblock]},
    'test-blockjob-txn': {'deps': [testblock]},
    'test-block-backend': {'deps': [testblock]},
    'test-block-iothread': {'deps': [testblock]},
    'test-image-locking': {'deps': [testblock], 'if': ['CONFIG_POSIX']},
    'test-write-threshold': {'deps': [testblock]},
    'test-crypto-hash': {'deps': [crypto]},
    'test-crypto-hmac': {'deps': [crypto]},
    'test-crypto-cipher': {'deps': [crypto]},
    'test-crypto-secret': {'deps': [crypto, keyutils]},
    'test-crypto-tlscredsx509': {
      'extra_src': files('crypto-tls-x509-helpers.c', 'pkix_asn1_tab.c'),
      'deps': [tasn1, crypto],
      'if': ['CONFIG_GNUTLS', 'CONFIG_TASN1']},
    'test-crypto-tlssession': {
      'extra_src': files('crypto-tls-x509-helpers.c', 'pkix_asn1_tab.c', 'crypto-tls-psk-helpers.c'),
      'deps': [tasn1, crypto],
      'if': ['CONFIG_GNUTLS', 'CONFIG_TASN1']},
    'test-authz-simple': {'deps': [authz]},
    'test-authz-list': {'deps': [authz]},
    'test-authz-listfile': {'deps': [authz]},
    'test-authz-pam': {'deps': [authz], 'if': ['CONFIG_AUTH_PAM']},
    'test-io-task': {'deps': [testblock]},
    'test-io-channel-socket': {
      'extra_src': files('socket-helpers.c', 'io-channel-helpers.c'),
      'deps': [io]},
    'test-io-channel-file': {
      'extra_src': files('io-channel-helpers.c'),
      'deps': [io]},
    'test-io-channel-tls': {
      'extra_src': files('io-channel-helpers.c', 'crypto-tls-x509-helpers.c', 'pkix_asn1_tab.c'),
      'deps': [tasn1, io, crypto],
      'if': ['CONFIG_GNUTLS', 'CONFIG_TASN1']},
    'test-io-channel-command': {
      'extra_src': files('io-channel-helpers.c'),
      'deps': [io]},
    'test-io-channel-buffer': {
      'extra_src': files('io-channel-helpers.c'),
      'deps': [io]},
    'test-crypto-ivgen': {'deps': [io]},
    'test-crypto-afsplit': {'deps': [io]},
    'test-crypto-xts': {'deps': [crypto, io], 'if': ['CONFIG_QEMU_PRIVATE_XTS']},
    'test-crypto-block': {'deps': [io]},
    'test-replication': {'deps': [testblock], 'if': ['CONFIG_REPLICATION', 'CONFIG_POSIX']},
  }
  if 'CONFIG_NETTLE' in config_host or 'CONFIG_GCRYPT' in config_host
    tests += {'test-crypto-pbkdf': {'deps': [io]}}
  endif
endif

if have_system
  tests += {
    'test-iov': {},
    'test-qmp-cmds': {'deps': [testqapi]},
    'test-xbzrle': {'deps': [migration]},
    'test-vmstate': {'deps': [migration, io], 'if': ['CONFIG_POSIX']},
    'test-timed-average': {},
    'test-util-filemonitor': {'if': ['CONFIG_INOTIFY1']},
    'test-util-sockets': {'extra_src': files('socket-helpers.c')},
    'test-base64': {},
    'test-bufferiszero': {},
  }
  # Some tests: test-char, test-qdev-global-props, and test-qga,
  # are not runnable under TSan due to a known issue.
  # https://github.com/google/sanitizers/issues/1116
  if 'CONFIG_TSAN' not in config_host
    tests += {
      'test-char': {'extra_src': files('socket-helpers.c'), 'deps': [qom, io, chardev]},
      'test-qdev-global-props': {'deps': [qom, hwcore, testqapi]}
    }
  endif
endif

if 'CONFIG_TSAN' not in config_host and 'CONFIG_GUEST_AGENT' in config_host
  tests += {'test-qga': {'extra_src': files('qtest/libqtest.c'), 'test_deps': [qga], 'if': ['CONFIG_GUEST_AGENT', 'CONFIG_LINUX']}}
endif

test_env = environment()
test_env.set('G_TEST_SRCDIR', meson.current_source_dir())
test_env.set('G_TEST_BUILDDIR', meson.current_build_dir())

foreach test_name, extra_args: tests
  check_if = true
  foreach t: extra_args.get('if', [])
    if t not in config_host
      check_if = false
      break
    endif
  endforeach
  if not check_if
    continue
  endif

  src = extra_args.get('src', [test_name + '.c'])
  extra_src = extra_args.get('extra_src', [])
  exe = executable(test_name, src + extra_src,
                   dependencies: [qemuutil] + extra_args.get('deps', []))

  suite = ['unit'] + extra_args.get('suite', [])
  test(test_name, exe,
       depends: extra_args.get('test_deps', []),
       env: test_env,
       args: ['--tap', '-k'],
       protocol: 'tap',
       suite: suite)
endforeach

if have_system and 'CONFIG_POSIX' in config_host
  subdir('qemu-iotests')
endif

test('decodetree', sh,
     args: [ files('decode/check.sh'), config_host['PYTHON'], files('../scripts/decodetree.py') ],
     workdir: meson.current_source_dir() / 'decode',
     suite: 'decodetree')

if 'CONFIG_TCG' in config_host
  subdir('fp')
  if 'CONFIG_PLUGIN' in config_host
    subdir('plugin')
  endif
endif

subdir('qapi-schema')
subdir('qtest')
