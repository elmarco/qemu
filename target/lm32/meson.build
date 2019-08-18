lm32_ss = ss.source_set()
lm32_ss.add(files(
  'cpu.c',
  'gdbstub.c',
  'helper.c',
  'lm32-semi.c',
  'op_helper.c',
  'translate.c',
))

lm32_softmmu_ss = ss.source_set()
lm32_softmmu_ss.add(files('machine.c'))

target_arch += {'lm32': [lm32_ss, lm32_softmmu_ss]}
