qos_src = files(
  'fw_cfg.c',
  'libqos.c',
  'malloc.c',
  'pci.c',
  'qgraph.c',
)

qos_src += files(
  'libqos-spapr.c',
  'malloc-spapr.c',
  'pci-spapr.c',
  'rtas.c',
)

qos_src += files(
  'ahci.c',
  'libqos-pc.c',
  'malloc-pc.c',
  'pci-pc.c',
)

qos_src += files('usb.c')

# devices
qos_src += files(
  'e1000e.c',
  'i2c-imx.c',
  'i2c-omap.c',
  'i2c.c',
  'sdhci.c',
  'tpci200.c',
  'virtio-balloon.c',
  'virtio-blk.c',
  'virtio-mmio.c',
  'virtio-net.c',
  'virtio-pci.c',
  'virtio-rng.c',
  'virtio-scsi.c',
  'virtio-serial.c',
  'virtio.c',
)

# machines
qos_src += files(
  'aarch64-xlnx-zcu102-machine.c',
  'arm-imx25-pdk-machine.c',
  'arm-n800-machine.c',
  'arm-raspi2-machine.c',
  'arm-sabrelite-machine.c',
  'arm-smdkc210-machine.c',
  'arm-virt-machine.c',
  'arm-xilinx-zynq-a9-machine.c',
  'ppc64_pseries-machine.c',
  'x86_64_pc-machine.c',
)

if 'CONFIG_VIRTFS' in config_host
  qos_src += files('virtio-9p.c')
endif

libqos = static_library(
  'libqos',
  qos_src,
  include_directories: inctests,
  dependencies: glib,
  build_by_default: false,
)

qos = declare_dependency(link_whole: libqos)
