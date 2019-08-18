specific_ss.add(when: 'CONFIG_SOFTMMU', if_true: files('accel.c'))
specific_ss.add(when: ['CONFIG_SOFTMMU', 'CONFIG_POSIX'], if_true: files('qtest.c'))

subdir('kvm')
subdir('tcg')
subdir('stubs')
