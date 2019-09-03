project('qemu', 'c', meson_version: '>=0.51.999')
cc = meson.get_compiler('c')

kconfig = import('unstable-kconfig')
ss = import('sourceset')
config_host = kconfig.load(meson.current_build_dir() / 'config-host.mak')

add_project_arguments(config_host['QEMU_CFLAGS'].split(),
                      language: 'c')
add_project_link_arguments(config_host['QEMU_CFLAGS'].split(),
                      language: 'c')
add_project_arguments(config_host['QEMU_INCLUDES'].split(),
                      language: 'c')

configure_file(input: files('scripts/ninjatool.py'),
               output: 'ninjatool',
               configuration: config_host)

m = cc.find_library('m', required: false)
util = cc.find_library('util', required: false)
socket = []
version_res = []
if host_machine.system() == 'windows'
  socket = cc.find_library('ws2_32')

  win = import('windows')
  version_res = win.compile_resources('version.rc',
                                      depend_files: files('pc-bios/qemu-nsis.ico'),
                                      include_directories: include_directories('.'))
endif
glib = declare_dependency(compile_args: config_host['GLIB_CFLAGS'].split(),
                          link_args: config_host['GLIB_LIBS'].split())
lttng = declare_dependency()
if 'CONFIG_TRACE_UST' in config_host
  lttng = declare_dependency(link_args: config_host['LTTNG_UST_LIBS'].split())
endif
urcubp = declare_dependency()
if 'CONFIG_TRACE_UST' in config_host
  urcubp = declare_dependency(link_args: config_host['URCU_BP_LIBS'].split())
endif
nettle = declare_dependency()
if 'CONFIG_NETTLE' in config_host
  nettle = declare_dependency(compile_args: config_host['NETTLE_CFLAGS'].split(),
                              link_args: config_host['NETTLE_LIBS'].split())
endif
gnutls = declare_dependency()
if 'CONFIG_GNUTLS' in config_host
  gnutls = declare_dependency(compile_args: config_host['GNUTLS_CFLAGS'].split(),
                              link_args: config_host['GNUTLS_LIBS'].split())
endif

target_dirs = config_host['TARGET_DIRS'].split()
have_user = false
have_system = false
foreach target : target_dirs
  have_user = have_user or target.endswith('-user')
  have_system = have_system or target.endswith('-softmmu')
endforeach
have_tools = 'CONFIG_TOOLS' in config_host
have_block = have_system or have_tools

# Generators

qapi_gen = find_program('scripts/qapi-gen.py')
qapi_gen_depends = [ meson.source_root() / 'scripts/qapi/events.py',
                     meson.source_root() / 'scripts/qapi/introspect.py',
                     meson.source_root() / 'scripts/qapi/types.py',
                     meson.source_root() / 'scripts/qapi/visit.py',
                     meson.source_root() / 'scripts/qapi/common.py',
                     meson.source_root() / 'scripts/qapi/doc.py',
                     meson.source_root() / 'scripts/qapi-gen.py' ]

# Collect sourcesets.

util_ss = ss.source_set()
stub_ss = ss.source_set()
trace_ss = ss.source_set()

# TODO: add each directory to the subdirs from its own meson.build, once
# we have those
trace_events_subdirs = [
  'accel/kvm',
  'accel/tcg',
  'crypto',
  'monitor',
]
if have_user
  trace_events_subdirs += [ 'linux-user' ]
endif
if have_block
  trace_events_subdirs += [
    'authz',
    'block',
    'io',
    'nbd',
    'scsi',
  ]
endif
if have_system
  trace_events_subdirs += [
    'chardev',
    'audio',
    'hw/9pfs',
    'hw/acpi',
    'hw/alpha',
    'hw/arm',
    'hw/audio',
    'hw/block',
    'hw/block/dataplane',
    'hw/char',
    'hw/dma',
    'hw/hppa',
    'hw/i2c',
    'hw/i386',
    'hw/i386/xen',
    'hw/ide',
    'hw/input',
    'hw/intc',
    'hw/isa',
    'hw/mem',
    'hw/mips',
    'hw/misc',
    'hw/misc/macio',
    'hw/net',
    'hw/nvram',
    'hw/pci',
    'hw/pci-host',
    'hw/ppc',
    'hw/rdma',
    'hw/rdma/vmw',
    'hw/s390x',
    'hw/scsi',
    'hw/sd',
    'hw/sparc',
    'hw/sparc64',
    'hw/timer',
    'hw/tpm',
    'hw/usb',
    'hw/vfio',
    'hw/virtio',
    'hw/watchdog',
    'hw/xen',
    'hw/gpio',
    'hw/riscv',
    'migration',
    'net',
    'ui',
  ]
endif
trace_events_subdirs += [
  'hw/display',
  'qapi',
  'qom',
  'target/arm',
  'target/hppa',
  'target/i386',
  'target/mips',
  'target/ppc',
  'target/riscv',
  'target/s390x',
  'target/sparc',
  'util',
]

genh = []
subdir('qapi')
subdir('qobject')
subdir('stubs')
subdir('trace')
subdir('util')
subdir('crypto')

# Build targets from sourcesets

stub_ss = stub_ss.apply(config_host, strict: false)

util_ss.add_all(trace_ss)
util_ss = util_ss.apply(config_host, strict: false)
libqemuutil = static_library('qemuutil',
                             sources: util_ss.sources() + stub_ss.sources(),
                             dependencies: [util_ss.dependencies(), m, glib, socket])
qemuutil = declare_dependency(link_with: libqemuutil,
                              sources: version_res)

# Other build targets

if have_tools
  if 'CONFIG_VHOST_USER' in config_host and 'CONFIG_LINUX' in config_host
    subdir('contrib/libvhost-user')
  endif
endif
