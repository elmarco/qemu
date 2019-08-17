i386_ss = ss.source_set()
i386_ss.add(files(
  'acpi-build.c',
  'fw_cfg.c',
  'kvmvapic.c',
  'multiboot.c',
  'pc.c',
  'pc_sysfw.c',
  'x86-iommu.c',
))

i386_ss.add(when: 'CONFIG_AMD_IOMMU', if_true: files('amd_iommu.c'))
i386_ss.add(when: 'CONFIG_I440FX', if_true: files('pc_piix.c'))
i386_ss.add(when: 'CONFIG_Q35', if_true: files('pc_q35.c'))
i386_ss.add(when: 'CONFIG_VMMOUSE', if_true: files('vmmouse.c'))
i386_ss.add(when: 'CONFIG_VMPORT', if_true: files('vmport.c'))
i386_ss.add(when: 'CONFIG_VTD', if_true: files('intel_iommu.c'))

subdir('kvm')
subdir('xen')

hw_arch += {'i386': i386_ss}
