py3 = import('python').find_installation()

rand = run_command(py3, '-c', 'import os; print(ord(os.urandom(1)))').stdout().strip()

benchmark_timeout = 300 # seconds

test_env = environment()
test_env.set('G_TEST_SRCDIR', meson.current_source_dir())
test_env.set('G_TEST_BUILDDIR', meson.current_build_dir())
test_env.set('G_DEBUG', 'gc-friendly')
test_env.set('MALLOC_CHECK_', '2')
test_env.set('MALLOC_PERTURB_', '@0@'.format(rand))

test_qapi_outputs = [
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

# meson doesn't like output in other directories...
subdir('include')

test_qapi_files = custom_target('Test QAPI files',
                                output: test_qapi_outputs,
                                input: files('qapi-schema/qapi-schema-test.json',
                                             'qapi-schema/include/sub-module.json',
                                             'qapi-schema/sub-sub-module.json'),
                                command: [ qapi_gen, '-o', meson.current_build_dir(),
                                           '-p', 'test-', '@INPUT0@' ],
                                depend_files: qapi_gen_depends)

libtestqapi = static_library('libtestqapi', sources: [test_qapi_files, test_qapi_outputs_extra])
testqapi = declare_dependency(link_with: libtestqapi)

testblock = declare_dependency(dependencies: [block], sources: files('iothread.c'))

libqtest = static_library('libqtest', sources: files('libqtest.c'), build_by_default: false)
qtest = declare_dependency(link_with: libqtest)

qhtbench = executable('qht-bench',
                      sources: files('qht-bench.c'),
                      dependencies: [qemuutil])

# common dependencies
test_deps = [qemuutil]

tests = {
  'check-qdict': {},
  'check-block-qdict': {},
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
  'test-qmp-cmds': {'deps': [testqapi]},
  'test-string-input-visitor': {'deps': [testqapi]},
  'test-string-output-visitor': {'deps': [testqapi]},
  'test-qmp-event': {'deps': [testqapi]},
  'test-opts-visitor': {'deps': [testqapi]},
  'test-visitor-serialization': {'deps': [testqapi]},
  'test-iov': {},
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
  'test-qdist': {},
  'test-qht': {'test_deps': [qhtbench]},
  'test-qht-par': {},
  'test-bitops': {},
  'test-bitcnt': {},
  'test-qdev-global-props': {'deps': [hwcore, qom, testqapi]},
  'check-qom-interface': {'deps': [qom]},
  'check-qom-proplist': {'deps': [qom]},
  'test-qemu-opts': {},
  'test-keyval': {'deps': [testqapi]},
  'test-timed-average': {},
  'test-util-filemonitor': {'if': ['CONFIG_INOTIFY1']},
  'test-util-sockets': {'extra_src': files('socket-helpers.c')},
  'test-base64': {},
  'test-logging': {},
  'test-bufferiszero': {},
  'test-uuid': {},
  'ptimer-test': {
    'extra_src': files('ptimer-test-stubs.c', meson.source_root() / 'hw/core/ptimer.c')},
  'test-qapi-util': {},
  'test-qgraph': {'extra_src': files('libqos/qgraph.c')},
}

if have_block
  tests += {
    'test-coroutine': {'deps': [testblock], 'suite': ['block']},
    'test-aio': {'deps': [testblock], 'suite': ['block']},
    'test-throttle': {'deps': [testblock], 'suite': ['block']},
    'test-thread-pool': {'deps': [testblock], 'suite': ['block']},
    'test-hbitmap': {'deps': [testblock], 'suite': ['block']},
    'test-bdrv-drain': {'deps': [testblock], 'suite': ['block']},
    'test-bdrv-graph-mod': {'deps': [testblock], 'suite': ['block']},
    'test-blockjob': {'deps': [testblock], 'suite': ['block']},
    'test-blockjob-txn': {'deps': [testblock], 'suite': ['block']},
    'test-block-backend': {'deps': [testblock], 'suite': ['block']},
    'test-block-iothread': {'deps': [testblock], 'suite': ['block']},
    'test-image-locking': {'deps': [testblock], 'suite': ['block'], 'if': ['CONFIG_POSIX']},
    'test-write-threshold': {'deps': [testblock], 'suite': ['block']},
    'test-crypto-hash': {'deps': [crypto], 'suite': ['block']},
    'benchmark-crypto-hash': {'deps': [crypto], 'suite': ['block', 'benchmark']},
    'test-crypto-hmac': {'deps': [crypto], 'suite': ['block']},
    'benchmark-crypto-hmac': {'deps': [crypto], 'suite': ['block', 'benchmark']},
    'test-crypto-cipher': {'deps': [crypto], 'suite': ['block']},
    'benchmark-crypto-cipher': {'deps': [crypto], 'suite': ['block', 'benchmark']},
    'test-crypto-secret': {'deps': [crypto], 'suite': ['block']},
    'test-crypto-tlscredsx509': {
      'extra_src': files('crypto-tls-x509-helpers.c', 'pkix_asn1_tab.c'),
      'deps': [tasn1, crypto], 'suite': ['block'],
      'if': ['CONFIG_GNUTLS', 'CONFIG_TASN1']},
    'test-crypto-tlssession': {
      'extra_src': files('crypto-tls-x509-helpers.c', 'pkix_asn1_tab.c', 'crypto-tls-psk-helpers.c'),
      'deps': [tasn1, crypto], 'suite': ['block'],
      'if': ['CONFIG_GNUTLS', 'CONFIG_TASN1']},
    'test-authz-simple': {'deps': [authz], 'suite': ['block']},
    'test-authz-list': {'deps': [authz], 'suite': ['block']},
    'test-authz-listfile': {'deps': [authz], 'suite': ['block']},
    'test-authz-pam': {'deps': [authz], 'suite': ['block'], 'if': ['CONFIG_AUTH_PAM']},
    'test-io-task': {'deps': [testblock], 'suite': ['block']},
    'test-io-channel-socket': {
      'extra_src': files('socket-helpers.c', 'io-channel-helpers.c'),
      'deps': [io], 'suite': ['block']},
    'test-io-channel-file': {
      'extra_src': files('io-channel-helpers.c'),
      'deps': [io], 'suite': ['block']},
    'test-io-channel-tls': {
      'extra_src': files('io-channel-helpers.c', 'crypto-tls-x509-helpers.c', 'pkix_asn1_tab.c'),
      'deps': [tasn1, io, crypto], 'suite': ['block'],
      'if': ['CONFIG_GNUTLS', 'CONFIG_TASN1']},
    'test-io-channel-command': {
      'extra_src': files('io-channel-helpers.c'),
      'deps': [io],
      'suite': ['block']},
    'test-io-channel-buffer': {
      'extra_src': files('io-channel-helpers.c'),
      'deps': [io],
      'suite': ['block']},
    'test-crypto-ivgen': {'deps': [io], 'suite': ['block']},
    'test-crypto-afsplit': {'deps': [io], 'suite': ['block']},
    'test-crypto-xts': {'deps': [io], 'suite': ['block']},
    'test-crypto-block': {'deps': [io], 'suite': ['block']},
    'test-replication': {'deps': [testblock], 'suite': ['block'], 'if': ['CONFIG_REPLICATION']},
  }

  if 'CONFIG_NETTLE' in config_host or 'CONFIG_GCRYPT' in config_host
    tests += {'test-crypto-pbkdf': {'deps': [io], 'suite': ['block']}}
  endif
endif

if have_system
  tests += {
    'test-xbzrle': {'deps': [migration]},
    'test-vmstate': {'deps': [migration]},
    'test-char': {'extra_src': files('socket-helpers.c'), 'deps': [chardev]},
  }
endif

if 'CONFIG_GUEST_AGENT' in config_host
  tests += {'test-qga': {'deps': [qtest], 'test_deps': qga, 'if': ['CONFIG_GUEST_AGENT']}}
endif

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
                   dependencies : test_deps + extra_args.get('deps', []))

  suite = ['unit'] + extra_args.get('suite', [])
  if 'benchmark' in suite
    assert('test_deps' not in extra_args, 'https://github.com/mesonbuild/meson/issues/5945')
    benchmark(test_name, exe,
              env: test_env,
              suite: suite,
              timeout: benchmark_timeout)
  else
    test(test_name, exe,
         depends: extra_args.get('test_deps', []),
         args: ['--tap'],
         env: test_env,
         suite: suite,
         protocol: 'tap')
  endif
endforeach

subdir('qapi-schema')
