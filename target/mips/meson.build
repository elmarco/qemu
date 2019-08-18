mips_ss = ss.source_set()
mips_ss.add(files(
  'cpu.c',
  'dsp_helper.c',
  'gdbstub.c',
  'helper.c',
  'lmi_helper.c',
  'msa_helper.c',
  'op_helper.c',
  'translate.c',
))
mips_ss.add(when: 'CONFIG_KVM', if_true: files('kvm.c'))

mips_softmmu_ss = ss.source_set()
mips_softmmu_ss.add(files(
  'cp0_timer.c',
  'machine.c',
  'mips-semi.c',
))

target_arch += {'mips': [mips_ss, mips_softmmu_ss]}
