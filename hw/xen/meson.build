softmmu_ss.add(when: 'CONFIG_XEN', if_true: files(
  'xen-backend.c',
  'xen-bus-helper.c',
  'xen-bus.c',
  'xen-common.c',
  'xen-legacy-backend.c',
  'xen_devconfig.c',
  'xen_pvdev.c',
))

specific_ss.add(when: 'CONFIG_XEN_PCI_PASSTHROUGH', if_true: files(
  'xen-host-pci-device.c',
  'xen_pt.c',
  'xen_pt_config_init.c',
  'xen_pt_graphics.c',
  'xen_pt_load_rom.c',
  'xen_pt_msi.c',
))
