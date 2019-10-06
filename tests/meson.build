py3 = import('python').find_installation()

rand = run_command(py3, '-c', 'import os; print(ord(os.urandom(1)))').stdout().strip()

slow_timeout = 300 # seconds

test_env = {
  'G_TEST_SRCDIR': meson.current_source_dir(),
  'G_TEST_BUILDDIR': meson.current_build_dir(),
  'G_DEBUG': 'gc-friendly',
  'MALLOC_CHECK_': '2',
  'MALLOC_PERTURB_': '@0@'.format(rand),
}

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

inctests = include_directories('.')
subdir('libqos')

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

executable('atomic_add-bench',
           sources: files('atomic_add-bench.c'),
           dependencies: [qemuutil],
           build_by_default: false)

executable('atomic64-bench',
           sources: files('atomic64-bench.c'),
           dependencies: [qemuutil],
           build_by_default: false)

if have_tools and 'CONFIG_VHOST_USER' in config_host and 'CONFIG_LINUX' in config_host
  executable('vhost-user-bridge',
             sources: files('vhost-user-bridge.c'),
             link_with: [libvhost_user],
             dependencies: [qemuutil],
             build_by_default: false)
endif

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
      'deps': [tasn1, crypto], 'suite': ['block', 'slow'],
      'if': ['CONFIG_GNUTLS', 'CONFIG_TASN1']},
    'test-crypto-tlssession': {
      'extra_src': files('crypto-tls-x509-helpers.c', 'pkix_asn1_tab.c', 'crypto-tls-psk-helpers.c'),
      'deps': [tasn1, crypto], 'suite': ['block', 'slow'],
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
              timeout: slow_timeout)
  else
    test(test_name, exe,
         depends: extra_args.get('test_deps', []),
         args: ['--tap'],
         env: test_env,
         suite: suite,
         protocol: 'tap')
  endif
endforeach

qos_tests_ss = ss.source_set()
qos_tests_ss.add(qos)
qos_tests_ss.add(files(
  'ac97-test.c',
  'ds1338-test.c',
  'e1000-test.c',
  'e1000e-test.c',
  'eepro100-test.c',
  'es1370-test.c',
  'ipoctal232-test.c',
  'megasas-test.c',
  'ne2000-test.c',
  'nvme-test.c',
  'pca9552-test.c',
  'pci-test.c',
  'pcnet-test.c',
  'sdhci-test.c',
  'spapr-phb-test.c',
  'tmp105-test.c',
  'usb-hcd-ohci-test.c',
  'virtio-blk-test.c',
  'virtio-net-test.c',
  'virtio-rng-test.c',
  'virtio-scsi-test.c',
  'virtio-serial-test.c',
  'virtio-test.c',
  'vmxnet3-test.c',
))

qos_tests_ss.add(when: 'CONFIG_VIRTFS', if_true: files('virtio-9p-test.c'))
qos_tests_ss.add(when: 'CONFIG_VHOST_NET_USER', if_true: [files('vhost-user-test.c'), chardev, io])
qos_tests = qos_tests_ss.apply(config_host, strict: false)

bios_tables_test_targets = ['i386']
# TODO: once aarch64 TCG is fixed on ARM 32 bit host, make test unconditional
if config_host['ARCH'] != 'arm'
  bios_tables_test_targets += ['aarch64']
endif

qtests = {
  'qmp-test': {},
  'qmp-cmd-test': {},
  'modules-test': {'if': ['CONFIG_MODULES']},
  'device-introspect-test': {},
  'cdrom-test': {'extra_src': files('boot-sector.c')},
  'machine-none-test': {},
  'qom-test': {},
  'test-hmp': {},
  'qos-test': {'extra_src': qos_tests.sources(), 'deps': qos_tests.dependencies()},
  'fdc-test': {'targets': ['i386']},
  'endianness-test': {'targets': ['i386', 'mips', 'mips64', 'mips64el', 'ppc', 'sh4', 'sh4eb', 'sparc64'], 'if': ['CONFIG_ISA_TESTDEV']},
  'rtl8139-test': {'targets': ['i386'], 'if': ['CONFIG_RTL8139_PCI'], 'deps': [qos]},
  'display-vga-test': {'targets': ['i386', 'ppc64', 'alpha', 'hppa', 'mips', 'mips64', 'mips64el'], 'if': ['CONFIG_VGA']},
  'intel-hda-test': {'targets': ['i386'], 'if': ['CONFIG_HDA']},
  'ivshmem-test': {
    'extra_src': files(meson.source_root() / 'contrib/ivshmem-server/ivshmem-server.c'),
    'targets': ['i386', 'ppc64'],
    'if': ['CONFIG_IVSHMEM_DEVICE'],
    'deps': [qos, rt],
  },
  'ide-test': {'targets': ['i386'], 'deps': [qos]},
  'hd-geo-test': {'targets': ['i386']},
  'boot-order-test': {'targets': ['i386', 'ppc'], 'deps': [qos]},
  'bios-tables-test': {'extra_src': ['boot-sector.c', 'acpi-utils.c'], 'targets': bios_tables_test_targets, 'deps': [qos]},
  'boot-serial-test': {
    'targets': ['alpha', 'hppa', 'm68k', 'microblaze', 'moxie', 'ppc', 'sparc', 'sparc64', 'arm', 'aarch64', 's390x', 'i386'],
    'deps': [qos],
    'if_i386': ['CONFIG_SGA'],
    'if_x86_64': ['CONFIG_SGA'],
  },
  'rtc-test': {'targets': ['i386']},
  'ipmi-kcs-test': {'targets': ['i386'], 'if': ['CONFIG_ISA_IPMI_KCS']},
  # Disabled temporarily as it fails intermittently especially under NetBSD VM
  # 'ipmi-bt-test': {'targets': ['i386'], 'if': ['CONFIG_ISA_IPMI_BT']},
  'i440fx-test': {'targets': ['i386'], 'deps': [qos]},
  'fw_cfg-test': {'targets': ['i386'], 'deps': [qos]},
  'device-plug-test': {'targets': ['i386', 's390x', 'ppc64'], 'if_ppc64': ['CONFIG_PSERIES']},
  'drive_del-test': {'targets': ['i386', 'ppc', 's390x']},
  'wdt_ib700-test': {'targets': ['i386'], 'if': ['CONFIG_WDT_IB700']},
  'tco-test': {'targets': ['i386'], 'deps': [qos]},
  'pvpanic-test': {'targets': ['i386'], 'if': ['CONFIG_PVPANIC']},
  'i82801b11-test': {'targets': ['i386'], 'if': ['CONFIG_I82801B11']},
  'ioh3420-test': {'targets': ['i386'], 'if': ['CONFIG_IOH3420']},
  'usb-hcd-uhci-test': {'targets': ['i386', 'ppc64'], 'deps': [qos], 'if': ['CONFIG_USB_UHCI']},
  'usb-hcd-ehci-test': {'targets': ['i386'], 'deps': [qos], 'if': ['CONFIG_USB_UHCI', 'CONFIG_USB_EHCI']},
  'usb-hcd-xhci-test': {'targets': ['i386', 'ppc64'], 'if': ['CONFIG_USB_XHCI_NEC'], 'deps': [qos]},
  'cpu-plug-test': {'targets': ['i386', 'ppc64', 's390x']},
  'q35-test': {'targets': ['i386'], 'deps': [qos]},
  'vmgenid-test': {'extra_src': ['boot-sector.c', 'acpi-utils.c'], 'targets': ['i386'], 'deps': [qos]},
  'tpm-crb-swtpm-test': {'extra_src': ['tpm-emu.c', 'tpm-util.c', 'tpm-tests.c'], 'targets': ['i386'], 'if': ['CONFIG_TPM_CRB'], 'deps': [io]},
  'tpm-crb-test': {'extra_src': ['tpm-emu.c'], 'targets': ['i386'], 'if': ['CONFIG_TPM_CRB'], 'deps': [io]},
  'tpm-tis-swtpm-test': {'extra_src': ['tpm-emu.c', 'tpm-util.c', 'tpm-tests.c'], 'targets': ['i386'], 'if': ['CONFIG_TPM_TIS'], 'deps': [io]},
  'tpm-tis-test': {'extra_src': ['tpm-emu.c'], 'targets': ['i386'], 'if': ['CONFIG_TPM_TIS'], 'deps': [io]},
  'test-filter-mirror': {'targets': ['i386', 'ppc64', 's390x'], 'if': ['CONFIG_POSIX']},
  'test-filter-redirector': {'targets': ['i386', 'ppc64', 's390x'], 'if': ['CONFIG_RTL8139_PCI']},
  'migration-test': {'targets': ['i386', 'ppc64', 's390x', 'aarch64']},
  'test-x86-cpuid-compat': {'targets': ['i386']},
  'numa-test': {'targets': ['i386', 'ppc64', 'aarch64']},
  'prom-env-test': {'targets': ['ppc', 'sparc', 'sparc64'], 'deps': [qos]},
  'm48t59-test': {'targets': ['ppc', 'sparc'], 'if': ['CONFIG_M48T59']},
  'pnv-xscom-test': {'targets': ['ppc64'], 'if': ['CONFIG_POWERNV']},
  'rtas-test': {'targets': ['ppc64'], 'if': ['CONFIG_PSERIES'], 'deps': [qos]},
  'microbit-test': {'targets': ['arm']},
  'm25p80-test': {'targets': ['arm']},
  'test-arm-mptimer': {'targets': ['arm']},
  'hexloader-test': {'targets': ['arm']},
  'pflash-cfi02-test': {'targets': ['arm'], 'if': ['CONFIG_PFLASH_CFI02']},
  'virtio-ccw-test': {'targets': ['s390x']},
}

if slirp.found()
  qtests += {
    'test-netfilter': {'targets': ['i386', 'ppc64', 's390x']},
    'pxe-test': {'extra_src': ['boot-sector.c'], 'targets': ['i386', 'ppc64', 's390x'], 'deps': [qos]},
  }
endif

if have_tools
  qtests += {'ahci-test': {'targets': ['i386'], 'if': ['CONFIG_TOOLS'], 'deps': [qos], 'test_deps': qemu_img}}
  test_env += {'QTEST_QEMU_IMG': qemu_img.full_path()}
endif

test_deps += [qtest]

foreach test_name, extra_args: qtests
  src = extra_args.get('src', [test_name + '.c'])
  extra_src = extra_args.get('extra_src', [])
  test_exe = executable(test_name, src + extra_src,
                        dependencies : test_deps + extra_args.get('deps', []),
                        build_by_default: false)

  foreach q: qemu
    check_if = true
    foreach t: extra_args.get('if', []) + extra_args.get('if_' + q['target-name'], [])
      if t not in q['config']
        check_if = false
        break
      endif
    endforeach
    if not check_if
      continue
    endif

    if q['target-type'] != 'system' or q['gui']
      continue
    endif

    test_targets = extra_args.get('targets', [])
    foreach t, alias: {'i386': 'x86_64',
                       'ppc': 'ppc64',
                       'microblaze': 'microblazeel',
                       'xtensa': 'xtensaeb'}
      if t in test_targets
        test_targets += [alias]
      endif
    endforeach

    if q['target-name'] not in test_targets
      continue
    endif

    test_env += {'QTEST_QEMU_BINARY': q['exe'].full_path()}

    test(test_name,
         test_exe,
         depends: extra_args.get('test_deps', []),
         args: ['--tap'],
         env: test_env,
         suite: ['qtest', q['target-name']] + extra_args.get('suite', []),
         protocol: 'tap',
         timeout: slow_timeout)
  endforeach
endforeach

subdir('qemu-iotests')

if have_system and have_tools and 'CONFIG_POSIX' in config_host
  check_block = find_program('check-block.sh')
  test('check-block', check_block,
       depends: [qemu_img, qemu_io, qemu_nbd, socket_scm_helper],
       suite: ['block'],
       timeout: slow_timeout)
endif

subdir('qapi-schema')
subdir('decode')

if 'CONFIG_TCG' in config_host
  # FPU Emulation tests (aka softfloat)
  subdir('fp')

  # The full test suite can take a bit of time, default to a quick run
  # "-l 2 -r all" can take more than a day for some operations and is best
  # run manually
  fp_tl = ['-l', '1', '-r', 'all']

  # Conversion Routines:
  # FIXME: i32_to_extF80 (broken), i64_to_extF80 (broken)
  #        ui32_to_f128 (not implemented), extF80_roundToInt (broken)
  #
  foreach desc, t: {
    'int-to-float': '''
       i32_to_f16 i64_to_f16
       i32_to_f32 i64_to_f32
       i32_to_f64 i64_to_f64
       i32_to_f128 i64_to_f128
    ''',
    'uint-to-float': '''
       ui32_to_f16 ui64_to_f16
       ui32_to_f32 ui64_to_f32
       ui32_to_f64 ui64_to_f64
       ui64_to_f128
    ''',
    'float-to-int': '''
      f16_to_i32 f16_to_i32_r_minMag
      f32_to_i32 f32_to_i32_r_minMag
      f64_to_i32 f64_to_i32_r_minMag
      extF80_to_i32 extF80_to_i32_r_minMag
      f128_to_i32 f128_to_i32_r_minMag
      f16_to_i64 f16_to_i64_r_minMag
      f32_to_i64 f32_to_i64_r_minMag
      f64_to_i64 f64_to_i64_r_minMag
      extF80_to_i64 extF80_to_i64_r_minMag
      f128_to_i64 f128_to_i64_r_minMag
    ''',
    'float-to-uint': '''
      f16_to_ui32 f16_to_ui32_r_minMag
      f32_to_ui32 f32_to_ui32_r_minMag
      f64_to_ui32 f64_to_ui32_r_minMag
      f128_to_ui32 f128_to_ui32_r_minMag
      f16_to_ui64 f16_to_ui64_r_minMag
      f32_to_ui64 f32_to_ui64_r_minMag
      f64_to_ui64 f64_to_ui64_r_minMag
      f128_to_ui64 f128_to_ui64_r_minMag
    ''',
    'round-to-integer': '''
      f16_roundToInt f32_roundToInt
      f64_roundToInt f128_roundToInt
    ''',
  }
    test(desc, fptest, args: fp_tl + t.split(), suite: ['fp', 'conv'])
  endforeach

  # Float Compare routines
  foreach op: ['eq', 'eq_signaling', 'le', 'le_quiet', 'lt_quiet']
    tests = 'f16_@0@ f32_@0@ f64_@0@ f128_@0@'.format(op).split()
    # FIXME: extF80_{le,lt}_quiet (broken)
    if not op.endswith('quiet')
      tests += ['extF80_' + op]
    endif
    test(op, fptest, args: fp_tl + tests, suite: ['fp', 'comp'])
  endforeach

  # Float Math operations
  foreach op: ['add', 'sub', 'mul', 'mulAdd', 'div', 'rem', 'sqrt']
    tests = 'f16_@0@ f32_@0@ f64_@0@ f128_@0@'.format(op).split()
    # FIXME: extF80_{mulAdd,rem} (missing, broken)
    if op not in ['mulAdd', 'rem']
      tests += ['extF80_' + op]
    endif
    if op == 'mulAdd'
      test(op, fptest, args: ['-l', '1'] + tests, suite: ['fp', 'math'], timeout: slow_timeout)
    else
      test(op, fptest, args: fp_tl + tests, suite: ['fp', 'math'], timeout: slow_timeout)
    endif
  endforeach

endif

# https://github.com/mesonbuild/meson/issues/3551
#  Source: https://docs.python.org/3/library/importlib.html#checking-if-a-module-can-be-imported
has_venv = true
foreach m: ['venv', 'ensurepip']
  t = 'import importlib.util; exit(1) if importlib.util.find_spec(\'' + m + '\') is None else exit(0)'
  if run_command(py3, '-c', t).returncode() != 0
    has_venv = false
    break
  endif
endforeach

if has_venv
  avocado_venv = custom_target(
    'avocado-venv',
    command: [find_program('avocado-venv.sh'), '@INPUT@', '@OUTPUT@', py3.path()],
    input: files('requirements.txt'),
    output: 'venv',
  )

  avocado_test = find_program('avocado-test.sh')
  foreach q: qemu
    if q['target-type'] != 'system' or q['gui']
      continue
    endif

    test('acceptance-' + q['target-name'],
         avocado_test,
         args: [
           avocado_venv,
           q['target-name'],
           meson.current_source_dir() / 'acceptance',
           meson.current_build_dir() / 'results'
         ],
         suite: ['acceptance', q['target-name']],
         protocol: 'tap',
         timeout: slow_timeout)
  endforeach
endif

subdir('migration')
