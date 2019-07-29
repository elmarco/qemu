chardev_ss = ss.source_set()
chardev_ss.add(files(
  'char-fe.c',
  'char-file.c',
  'char-io.c',
  'char-mux.c',
  'char-null.c',
  'char-pipe.c',
  'char-ringbuf.c',
  'char-serial.c',
  'char-socket.c',
  'char-stdio.c',
  'char-udp.c',
  'char.c',
))
chardev_ss.add(when: 'CONFIG_POSIX', if_true: files(
  'char-fd.c',
  'char-parallel.c',
  'char-pty.c',
))
chardev_ss.add(when: 'CONFIG_WIN32', if_true: files(
  'char-console.c',
  'char-win-stdio.c',
  'char-win.c',
))

chardev_ss = chardev_ss.apply(config_host, strict: false)
libchardev = static_library('chardev', chardev_ss.sources(),
                            dependencies: [crypto, io, qom],
                            link_with: libqemuutil,
                            name_suffix: 'fa',
                            build_by_default: false)

chardev = declare_dependency(link_with: libchardev)

softmmu_ss.add(files('msmouse.c', 'wctablet.c', 'testdev.c'))
softmmu_ss.add(when: [sdl, brlapi], if_true: files('baum.c'))
softmmu_ss.add(when: spice, if_true: files('spice.c'))
softmmu_ss.add(chardev)
