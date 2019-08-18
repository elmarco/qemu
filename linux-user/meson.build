linux_user_ss.add(files(
  'elfload.c',
  'exit.c',
  'fd-trans.c',
  'linuxload.c',
  'main.c',
  'mmap.c',
  'safe-syscall.S',
  'signal.c',
  'strace.c',
  'syscall.c',
  'uaccess.c',
  'uname.c',
))
linux_user_ss.add(rt)

linux_user_ss.add(when: 'TARGET_AARCH64', if_true: files('arm/semihost.c'))
linux_user_ss.add(when: 'TARGET_ARM', if_true: files('arm/semihost.c'))
linux_user_ss.add(when: 'TARGET_HAS_BFLT', if_true: files('flatload.c'))
linux_user_ss.add(when: 'TARGET_I386', if_true: files('vm86.c'))

subdir('arm/nwfpe')
