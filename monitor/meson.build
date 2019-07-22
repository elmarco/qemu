softmmu_ss.add(files(
  'hmp-cmds.c',
  'hmp.c',
  'monitor.c',
  'qmp-cmds.c',
  'qmp.c',
))

specific_ss.add(when: 'CONFIG_SOFTMMU', if_true: files('misc.c'))
