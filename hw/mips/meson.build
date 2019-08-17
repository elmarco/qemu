mips_ss = ss.source_set()
mips_ss.add(files('addr.c', 'mips_int.c'))
mips_ss.add(when: 'CONFIG_FULONG', if_true: files('mips_fulong2e.c'))
mips_ss.add(when: 'CONFIG_JAZZ', if_true: files('mips_jazz.c'))
mips_ss.add(when: 'CONFIG_MALTA', if_true: files('gt64xxx_pci.c', 'mips_malta.c'))
mips_ss.add(when: 'CONFIG_MIPSSIM', if_true: files('mips_mipssim.c'))
mips_ss.add(when: 'CONFIG_MIPS_BOSTON', if_true: files('boston.c'))
mips_ss.add(when: 'CONFIG_MIPS_CPS', if_true: files('cps.c'))
mips_ss.add(when: 'CONFIG_R4K', if_true: files('mips_r4k.c'))

hw_arch += {'mips': mips_ss}
