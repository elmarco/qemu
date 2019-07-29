project('qemu', 'c', meson_version: '>=0.51.999')
cc = meson.get_compiler('c')

kconfig = import('unstable-kconfig')
ss = import('sourceset')
config_host = kconfig.load(meson.current_build_dir() / 'config-host.mak')
config_all_disas = kconfig.load(meson.current_build_dir() / 'config-all-disas.mak')

enable_modules = 'CONFIG_MODULES' in config_host

add_project_arguments(config_host['QEMU_CFLAGS'].split(),
                      language: ['c', 'objc'])
add_project_arguments(config_host['QEMU_CXXFLAGS'].split(),
                      language: 'cpp')
add_project_link_arguments(config_host['QEMU_CFLAGS'].split(),
                      language: 'c')
add_project_arguments(config_host['QEMU_INCLUDES'].split(),
                      language: ['c', 'cpp', 'objc'])

qemu_version_cmd = [find_program('scripts/qemu-version.sh'),
                    meson.current_source_dir(),
                    config_host['PKGVERSION'], config_host['VERSION']]
qemu_version = custom_target('QEMU version',
                             output: 'qemu-version.h',
                             command: qemu_version_cmd,
                             capture: true,
                             build_by_default: true,
                             build_always_stale: true)

configure_file(input: files('scripts/ninjatool.py'),
               output: 'ninjatool',
               configuration: config_host)

m = cc.find_library('m', required: false)
util = cc.find_library('util', required: false)
socket = []
version_res = []
coref = []
iokit = []
cocoa = []
hvf = []
if host_machine.system() == 'windows'
  socket = cc.find_library('ws2_32')

  win = import('windows')
  version_res = win.compile_resources('version.rc',
                                      depend_files: files('pc-bios/qemu-nsis.ico'),
                                      include_directories: include_directories('.'))
elif host_machine.system() == 'darwin'
  add_languages('objc', required: false)
  coref = dependency('appleframeworks', modules: 'CoreFoundation')
  iokit = dependency('appleframeworks', modules: 'IOKit')
  cocoa = dependency('appleframeworks', modules: 'Cocoa')
  hvf = dependency('appleframeworks', modules: 'Hypervisor')
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
pixman = declare_dependency(compile_args: config_host['PIXMAN_CFLAGS'].split(),
                            link_args: config_host['PIXMAN_LIBS'].split())
pam = declare_dependency()
if 'CONFIG_AUTH_PAM' in config_host
  pam = cc.find_library('pam')
endif
libaio = cc.find_library('aio', required: false)
zlib = declare_dependency()
if 'CONFIG_ZLIB' in config_host
  zlib = declare_dependency(compile_args: config_host['ZLIB_CFLAGS'].split(),
                            link_args: config_host['ZLIB_LIBS'].split())
endif
libxml2 = declare_dependency()
if 'CONFIG_LIBXML2' in config_host
  libxml2 = declare_dependency(compile_args: config_host['LIBXML2_CFLAGS'].split(),
                               link_args: config_host['LIBXML2_LIBS'].split())
endif
libnfs = declare_dependency()
if 'CONFIG_LIBNFS' in config_host
  libnfs = declare_dependency(link_args: config_host['LIBNFS_LIBS'].split())
endif
libattr = declare_dependency()
if 'CONFIG_ATTR' in config_host
  libattr = declare_dependency(link_args: config_host['LIBATTR_LIBS'].split())
endif
libcap = dependency('libcap', required: false)
libcap_ng = declare_dependency()
if 'CONFIG_LIBCAP' in config_host
  libcap_ng = declare_dependency(link_args: config_host['LIBCAP_NG_LIBS'].split())
endif
xkbcommon = dependency('xkbcommon', required: false)
pulse = declare_dependency()
if 'CONFIG_LIBPULSE' in config_host
  pulse = declare_dependency(compile_args: config_host['PULSE_CFLAGS'].split(),
                             link_args: config_host['PULSE_LIBS'].split())
endif
alsa = declare_dependency()
if 'CONFIG_ALSA' in config_host
  alsa = declare_dependency(compile_args: config_host['ALSA_CFLAGS'].split(),
                            link_args: config_host['ALSA_LIBS'].split())
endif
spice = declare_dependency()
if 'CONFIG_SPICE' in config_host
  spice = declare_dependency(compile_args: config_host['SPICE_CFLAGS'].split(),
                             link_args: config_host['SPICE_LIBS'].split())
endif
rt = cc.find_library('rt', required: false)
libmpathpersist = declare_dependency()
if config_host.has_key('CONFIG_MPATH')
  libmpathpersist = cc.find_library('mpathpersist')
endif
libiscsi = declare_dependency()
if 'CONFIG_LIBISCSI' in config_host
  libiscsi = declare_dependency(compile_args: config_host['LIBISCSI_CFLAGS'].split(),
                                link_args: config_host['LIBISCSI_LIBS'].split())
endif
gbm = declare_dependency()
if 'CONFIG_GBM' in config_host
  gbm = declare_dependency(compile_args: config_host['GBM_CFLAGS'].split(),
                           link_args: config_host['GBM_LIBS'].split())
endif
virgl = declare_dependency()
if 'CONFIG_VIRGL' in config_host
  virgl = declare_dependency(compile_args: config_host['VIRGL_CFLAGS'].split(),
                             link_args: config_host['VIRGL_LIBS'].split())
endif
curl = declare_dependency()
if 'CONFIG_CURL' in config_host
  curl = declare_dependency(compile_args: config_host['CURL_CFLAGS'].split(),
                            link_args: config_host['CURL_LIBS'].split())
endif
libudev = declare_dependency()
if 'CONFIG_LIBUDEV' in config_host
  libudev = declare_dependency(link_args: config_host['LIBUDEV_LIBS'].split())
endif
brlapi = declare_dependency()
if 'CONFIG_BRLAPI' in config_host
  brlapi = declare_dependency(link_args: config_host['BRLAPI_LIBS'].split())
endif
sdl = declare_dependency()
if 'CONFIG_SDL' in config_host
  sdl = declare_dependency(compile_args: config_host['SDL_CFLAGS'].split(),
                           link_args: config_host['SDL_LIBS'].split())
endif
rbd = declare_dependency()
if 'CONFIG_RBD' in config_host
  rbd = declare_dependency(link_args: config_host['RBD_LIBS'].split())
endif
glusterfs = declare_dependency()
if 'CONFIG_GLUSTERFS' in config_host
  glusterfs = declare_dependency(compile_args: config_host['GLUSTERFS_CFLAGS'].split(),
                                 link_args: config_host['GLUSTERFS_LIBS'].split())
endif
vxhs = declare_dependency()
if 'CONFIG_VXHS' in config_host
  vxhs = declare_dependency(link_args: config_host['VXHS_LIBS'].split())
endif
libssh = declare_dependency()
if 'CONFIG_LIBSSH' in config_host
  libssh = declare_dependency(compile_args: config_host['LIBSSH_CFLAGS'].split(),
                              link_args: config_host['LIBSSH_LIBS'].split())
endif
libbzip2 = declare_dependency()
if 'CONFIG_BZIP2' in config_host
  libbzip2 = declare_dependency(link_args: config_host['BZIP2_LIBS'].split())
endif
liblzfse = declare_dependency()
if 'CONFIG_LZFSE' in config_host
  liblzfse = declare_dependency(link_args: config_host['LZFSE_LIBS'].split())
endif
oss = declare_dependency()
if 'CONFIG_AUDIO_OSS' in config_host
  oss = declare_dependency(link_args: config_host['OSS_LIBS'].split())
endif
dsound = declare_dependency()
if 'CONFIG_AUDIO_DSOUND' in config_host
  dsound = declare_dependency(link_args: config_host['DSOUND_LIBS'].split())
endif
coreaudio = declare_dependency()
if 'CONFIG_AUDIO_COREAUDIO' in config_host
  coreaudio = declare_dependency(link_args: config_host['COREAUDIO_LIBS'].split())
endif
opengl = declare_dependency()
if 'CONFIG_OPENGL' in config_host
  opengl = declare_dependency(link_args: config_host['OPENGL_LIBS'].split())
else
endif
gtk = declare_dependency()
if 'CONFIG_GTK' in config_host
  gtk = declare_dependency(compile_args: config_host['GTK_CFLAGS'].split(),
                              link_args: config_host['GTK_LIBS'].split())
endif
vte = declare_dependency()
if 'CONFIG_VTE' in config_host
  vte = declare_dependency(compile_args: config_host['VTE_CFLAGS'].split(),
                           link_args: config_host['VTE_LIBS'].split())
endif
x11 = declare_dependency()
if 'CONFIG_X11' in config_host
  x11 = declare_dependency(compile_args: config_host['X11_CFLAGS'].split(),
                           link_args: config_host['X11_LIBS'].split())
endif
curses = declare_dependency()
if 'CONFIG_CURSES' in config_host
  curses = declare_dependency(compile_args: config_host['CURSES_CFLAGS'].split(),
                              link_args: config_host['CURSES_LIBS'].split())
endif
iconv = declare_dependency()
if 'CONFIG_ICONV' in config_host
  iconv = declare_dependency(compile_args: config_host['ICONV_CFLAGS'].split(),
                             link_args: config_host['ICONV_LIBS'].split())
endif
gio = declare_dependency()
if 'CONFIG_GIO' in config_host
  gio = declare_dependency(compile_args: config_host['GIO_CFLAGS'].split(),
                           link_args: config_host['GIO_LIBS'].split())
endif
png = declare_dependency()
if 'CONFIG_VNC_PNG' in config_host
  png = declare_dependency(compile_args: config_host['PNG_CFLAGS'].split(),
                           link_args: config_host['PNG_LIBS'].split())
endif
jpeg = declare_dependency()
if 'CONFIG_VNC_JPEG' in config_host
  jpeg = declare_dependency(compile_args: config_host['JPEG_CFLAGS'].split(),
                            link_args: config_host['JPEG_LIBS'].split())
endif
sasl = declare_dependency()
if 'CONFIG_VNC_SASL' in config_host
  sasl = declare_dependency(compile_args: config_host['SASL_CFLAGS'].split(),
                            link_args: config_host['SASL_LIBS'].split())
endif
bluez = declare_dependency()
if config_host.has_key('CONFIG_BLUEZ')
  bluez = declare_dependency(compile_args: config_host['BLUEZ_CFLAGS'].split())
endif
seccomp = declare_dependency()
if config_host.has_key('CONFIG_SECCOMP')
  seccomp = declare_dependency(compile_args: config_host['SECCOMP_CFLAGS'].split(),
                               link_args: config_host['SECCOMP_LIBS'].split())
endif

create_config = find_program('scripts/create_config')
minikconf = find_program('scripts/minikconf.py')
target_dirs = config_host['TARGET_DIRS'].split()
have_user = false
have_system = false
target_devices_kconfs = []
target_devices_h = []
foreach target : target_dirs
  have_user = have_user or target.endswith('-user')
  config_target = kconfig.load(meson.current_build_dir() / target / 'config-target.mak')

  if target.endswith('-softmmu')
    have_system = true

    base_kconfig = []
    if 'CONFIG_KVM' in config_target
      base_kconfig += 'CONFIG_KVM=y'
    endif
    if 'CONFIG_XEN' in config_target
      base_kconfig += 'CONFIG_XEN=y'
    endif
    if 'CONFIG_TPM' in config_host
      base_kconfig += 'CONFIG_TPM=y'
    endif
    if 'CONFIG_SPICE' in config_host
      base_kconfig += 'CONFIG_SPICE=y'
    endif
    if 'CONFIG_IVSHMEM' in config_host
      base_kconfig += 'CONFIG_IVSHMEM=y'
    endif
    if 'CONFIG_OPENGL' in config_host
      base_kconfig += 'CONFIG_OPENGL=y'
    endif
    if 'CONFIG_X11' in config_host
      base_kconfig += 'CONFIG_X11=y'
    endif
    if 'CONFIG_VHOST_USER' in config_host
      base_kconfig += 'CONFIG_VHOST_USER=y'
    endif
    if 'CONFIG_VIRTFS' in config_host
      base_kconfig += 'CONFIG_VIRTFS=y'
    endif
    if 'CONFIG_LINUX' in config_host
      base_kconfig += 'CONFIG_LINUX=y'
    endif
    if 'CONFIG_PVRDMA' in config_host
      base_kconfig += 'CONFIG_PVRDMA=y'
    endif

    config_devices_mak = target + '-config-devices.mak'
    config_devices_mak = configure_file(
      input: ['default-configs' / target + '.mak', 'Kconfig.host', 'hw/Kconfig'],
      output: config_devices_mak,
      depfile: config_devices_mak + '.d',
      capture: true,
      command: [minikconf, config_host['CONFIG_MINIKCONF_MODE'],
                config_devices_mak, '@DEPFILE@', '@INPUT@',
                base_kconfig])
    target_devices_kconfs += config_devices_mak
    config_devices_h = target + '-config-devices.h'
    target_devices_h += custom_target(
      config_devices_h,
      input: config_devices_mak,
      output: config_devices_h,
      capture: true,
      command: [create_config, '@INPUT@'])
  endif
endforeach
have_tools = 'CONFIG_TOOLS' in config_host
have_block = have_system or have_tools

grepy = find_program('scripts/grepy.sh')
# This configuration is used to build files that are shared by
# multiple binaries, and then extracted out of the "common"
# static_library target.
#
# We do not use all_sources()/all_dependencies(), because it would
# build literally all source files, including devices only used by
# targets that are not built for this compilation.  The CONFIG_ALL
# pseudo symbol replaces it.

config_all = {}
if target_devices_kconfs.length() > 0
  config_all_devices = configure_file(
    output: 'config-all-devices.mak',
    input: target_devices_kconfs,
    capture: true,
    command: [grepy, '@INPUT@'],
  )
  config_all += kconfig.load(config_all_devices)
endif
config_all += config_host
config_all += config_all_disas
config_all += {
  'CONFIG_XEN': config_host.has_key('CONFIG_XEN_BACKEND'),
  'CONFIG_SOFTMMU': have_system,
  'CONFIG_USER_ONLY': have_user,
  'CONFIG_ALL': true,
}

# Generators

hxtool = find_program('scripts/hxtool')
shaderinclude = find_program('scripts/shaderinclude.pl')
qapi_gen = find_program('scripts/qapi-gen.py')
qapi_gen_depends = [ meson.source_root() / 'scripts/qapi/events.py',
                     meson.source_root() / 'scripts/qapi/introspect.py',
                     meson.source_root() / 'scripts/qapi/types.py',
                     meson.source_root() / 'scripts/qapi/visit.py',
                     meson.source_root() / 'scripts/qapi/common.py',
                     meson.source_root() / 'scripts/qapi/doc.py',
                     meson.source_root() / 'scripts/qapi-gen.py' ]

config_host_h = custom_target('config-host.h',
                              input: meson.current_build_dir() / 'config-host.mak',
                              output: 'config-host.h',
                              capture: true,
                              command: [create_config, '@INPUT@'])

hxdep = []
hx_headers = [
  ['qemu-options.hx', 'qemu-options.def'],
  ['qemu-img-cmds.hx', 'qemu-img-cmds.h'],
]
if have_system
  hx_headers += [
    ['hmp-commands.hx', 'hmp-commands.h'],
    ['hmp-commands-info.hx', 'hmp-commands-info.h'],
  ]
endif
foreach d : hx_headers
  hxdep += custom_target(d[1],
                input: files(d[0]),
                output: d[1],
                capture: true,
                build_by_default: true, # to be removed when added to a target
                command: [hxtool, '-h', '@INPUT0@'])
endforeach

foreach d : [
  ['qemu-options.hx', 'qemu-options.texi'],
  ['hmp-commands.hx', 'qemu-monitor.texi'],
  ['hmp-commands-info.hx', 'qemu-monitor-info.texi'],
  ['qemu-img-cmds.hx', 'qemu-img-cmds.texi'],
]
  custom_target(d[1],
                input: files(d[0]),
                output: d[1],
                capture: true,
                build_by_default: true, # to be removed when added to a target
                command: [hxtool, '-t', '@INPUT0@'])
endforeach

# Collect sourcesets.

util_ss = ss.source_set()
stub_ss = ss.source_set()
trace_ss = ss.source_set()
block_ss = ss.source_set()
common_ss = ss.source_set()
softmmu_ss = ss.source_set()
user_ss = ss.source_set()
specific_ss = ss.source_set()

modules = {}

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

genh = [config_host_h]
subdir('qapi')
subdir('qobject')
subdir('stubs')
subdir('trace')
subdir('util')
subdir('crypto')
subdir('ui')


if enable_modules
  libmodulecommon = static_library('module-common', files('module-common.c') + genh, pic: true, c_args: '-DBUILD_DSO')
  modulecommon = declare_dependency(link_whole: libmodulecommon, compile_args: '-DBUILD_DSO')
endif

# Build targets from sourcesets

stub_ss = stub_ss.apply(config_host, strict: false)

util_ss.add_all(trace_ss)
util_ss = util_ss.apply(config_host, strict: false)
libqemuutil = static_library('qemuutil',
                             sources: util_ss.sources() + stub_ss.sources(),
                             dependencies: [util_ss.dependencies(), m, glib, socket])
qemuutil = declare_dependency(link_with: libqemuutil,
                              sources: version_res)

subdir('qom')
subdir('audio')
subdir('authz')
subdir('io')
subdir('chardev')
subdir('fsdev')

block_ss.add(files(
  'block.c',
  'blockjob.c',
  'job.c',
  'qemu-io-cmds.c',
))
block_ss.add(when: 'CONFIG_REPLICATION', if_true: files('replication.c'))

subdir('nbd')
subdir('scsi')
subdir('block')

softmmu_ss.add(files(
  'blockdev-nbd.c',
  'blockdev.c',
  'bootdevice.c',
  'device-hotplug.c',
  'dma-helpers.c',
  'iothread.c',
  'job-qmp.c',
  'qdev-monitor.c',
  'vl.c',
), sdl)

softmmu_ss.add(files('bt-host.c', 'bt-vhci.c'), bluez)

softmmu_ss.add(when: 'CONFIG_WIN32', if_true: files('os-win32.c'))
softmmu_ss.add(when: 'CONFIG_POSIX', if_true: files('os-posix.c'))
softmmu_ss.add(when: 'CONFIG_TPM', if_true: files('tpm.c'))
softmmu_ss.add(when: 'CONFIG_SECCOMP', if_true: [files('qemu-seccomp.c'), seccomp])
softmmu_ss.add(when: 'CONFIG_FDT',  if_true: files('device_tree.c'))

common_ss.add(files('cpus-common.c'))

mods = []
block_mods = []
softmmu_mods = []
foreach d, list : modules
  foreach m : list
    if enable_modules and host_machine.system() != 'windows'
      sl = static_library(d + '-' + m[0], m[1], dependencies: [m[2], modulecommon], pic: true)
      if d == 'block'
        block_mods += sl
      else
        softmmu_mods += sl
      endif
      mods += {'dir': d, 'name': m[0], 'lib': [sl, libmodulecommon], 'deps': m[2]}
    else
      if d == 'block'
        block_ss.add(when: m[2], if_true: m[1])
      else
        softmmu_ss.add(when: m[2], if_true: m[1])
      endif
    endif
  endforeach
endforeach

nm = find_program('nm')
undefsym = find_program('scripts/undefsym.sh')
block_syms = custom_target('block.syms', output: 'block.syms',
                             input: [libqemuutil, block_mods],
                             capture: true,
                             command: [undefsym, nm, '@INPUT@'])
qemu_syms = custom_target('qemu.syms', output: 'qemu.syms',
                             input: [libqemuutil, softmmu_mods],
                             capture: true,
                             command: [undefsym, nm, '@INPUT@'])

block_ss = block_ss.apply(config_host, strict: false)
libblock = static_library('block', block_ss.sources(),
                          dependencies: [authz, crypto, io, block_ss.dependencies()],
                          link_depends: block_syms,
                          link_with: libqemuutil,
                          name_suffix: 'fa',
                          build_by_default: false)

block = declare_dependency(link_whole: libblock, link_args: '@block.syms')

foreach m : mods
  shared_module(m['dir'] + '-' + m['name'],
                name_prefix: '',
                link_whole: [m['lib']])
endforeach

softmmu_ss.add(block)
common_ss.add_all(when: 'CONFIG_SOFTMMU', if_true: softmmu_ss)
common_ss.add_all(when: 'CONFIG_USER_ONLY', if_true: user_ss)

common_all = common_ss.apply(config_all, strict: false)
common_all = static_library('common',
                            sources: common_all.sources(),
                            dependencies: common_all.dependencies(),
                            name_suffix: 'fa')

i = 0
foreach target : target_dirs
  config_target = kconfig.load(meson.current_build_dir() / target / 'config-target.mak')
  config_target += config_host

  target_inc = [include_directories('target' / config_target['TARGET_BASE_ARCH'])]
  if host_machine.system() == 'linux'
    target_inc += include_directories('linux-headers')
  endif
  if target.endswith('-softmmu')
    config_target += kconfig.load(target_devices_kconfs[i])
    i += 1
  else
    target_inc += include_directories(
      'linux-user',
      'linux-user' / config_target['TARGET_ABI_DIR'],
      'linux-user' / 'host' / config_target['ARCH'],
    )
  endif
  target_common = common_ss.apply(config_target, strict: false)
  objects = common_all.extract_objects(target_common.sources())
  deps = target_common.dependencies()

  # TODO: Change to generator once obj-y goes away
  config_target_h = custom_target(target + '-config-target.h',
                              input: meson.current_build_dir() / target / 'config-target.mak',
                              output: target + '-config-target.h',
                              capture: true,
                              command: [create_config, '@INPUT@'])

  target_specific = specific_ss.apply(config_target, strict: false)
  static_library('qemu-' + target,
                 sources: target_specific.sources() + [config_target_h],
                 dependencies: target_specific.dependencies() + deps,
                 objects: objects,
                 include_directories: target_inc,
                 c_args: ['-DNEED_CPU_H',
                          '-DCONFIG_TARGET="@0@-config-target.h"'.format(target),
                          '-DCONFIG_DEVICES="@0@-config-devices.h"'.format(target)],
                 name_suffix: 'fa')
endforeach

# Other build targets

if 'CONFIG_GUEST_AGENT' in config_host
  subdir('qga')
endif

if have_tools
  executable('qemu-img', [files('qemu-img.c'), hxdep], dependencies: [block, qemuutil])
  if host_machine.system() == 'linux' or host_machine.system() == 'sunos' or host_machine.system().endswith('bsd')
    executable('qemu-nbd', files('qemu-nbd.c'), dependencies: [block, qemuutil])
  endif
  executable('qemu-io', files('qemu-io.c'), dependencies: [block, qemuutil])

  subdir('contrib/rdmacm-mux')
  subdir('contrib/elf2dmp')

  if xkbcommon.found()
    executable('qemu-keymap', files('qemu-keymap.c', 'ui/input-keymap.c'),
               dependencies: [qemuutil, xkbcommon])
  endif

  executable('qemu-edid', files('qemu-edid.c', 'hw/display/edid-generate.c'),
             dependencies: qemuutil)

  if 'CONFIG_VHOST_USER' in config_host and 'CONFIG_LINUX' in config_host
    subdir('contrib/libvhost-user')
    subdir('contrib/vhost-user-blk')
    subdir('contrib/vhost-user-gpu')
    subdir('contrib/vhost-user-input')
    subdir('contrib/vhost-user-scsi')
  endif

  if host_machine.system() == 'linux'
    executable('qemu-bridge-helper', files('qemu-bridge-helper.c'),
               dependencies: [qemuutil, libcap_ng])

    executable('qemu-pr-helper', files('scsi/qemu-pr-helper.c', 'scsi/utils.c'),
               dependencies: [authz, crypto, io, qom, qemuutil,
                              libcap_ng, libudev, libmpathpersist])
  endif

  if 'CONFIG_IVSHMEM' in config_host
    subdir('contrib/ivshmem-client')
    subdir('contrib/ivshmem-server')
  endif
endif

subdir('pc-bios')
