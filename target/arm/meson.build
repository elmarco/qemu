gen = [
  decodetree.process('sve.decode', extra_args: '--decode=disas_sve'),
  decodetree.process('vfp.decode', extra_args: '--static-decode=disas_vfp'),
  decodetree.process('vfp-uncond.decode', extra_args: '--static-decode=disas_vfp_uncond'),
]

arm_ss = ss.source_set()
arm_ss.add(gen)
arm_ss.add(files(
  'cpu.c',
  'crypto_helper.c',
  'debug_helper.c',
  'gdbstub.c',
  'helper.c',
  'iwmmxt_helper.c',
  'm_helper.c',
  'neon_helper.c',
  'op_helper.c',
  'tlb_helper.c',
  'translate.c',
  'vec_helper.c',
  'vfp_helper.c',
))
arm_ss.add(zlib)

arm_ss.add(when: 'CONFIG_TCG', if_true: files('arm-semi.c'))

kvm_ss = ss.source_set()
kvm_ss.add(when: 'TARGET_AARCH64', if_true: 'kvm64.c', if_false: 'kvm32.c')
arm_ss.add_all(when: 'CONFIG_KVM', if_true: kvm_ss)
arm_ss.add(when: 'CONFIG_KVM', if_true: files('kvm.c'), if_false: files('kvm-stub.c'))

arm_ss.add(when: 'TARGET_AARCH64', if_true: files(
  'cpu64.c',
  'gdbstub64.c',
  'helper-a64.c',
  'pauth_helper.c',
  'sve_helper.c',
  'translate-a64.c',
  'translate-sve.c',
))

arm_softmmu_ss = ss.source_set()
arm_softmmu_ss.add(files(
  'arch_dump.c',
  'arm-powerctl.c',
  'machine.c',
  'monitor.c',
  'psci.c',
))

target_arch += {'arm': [arm_ss, arm_softmmu_ss]}
