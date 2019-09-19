bzip2 = find_program('bzip2')

fds = [
  'edk2-aarch64-code.fd',
  'edk2-arm-code.fd',
  'edk2-arm-vars.fd',
  'edk2-i386-code.fd',
  'edk2-i386-secure-code.fd',
  'edk2-i386-vars.fd',
  'edk2-x86_64-code.fd',
  'edk2-x86_64-secure-code.fd',
]

install_blobs = 'INSTALL_BLOBS' in config_host

foreach f: fds
  custom_target(f,
                output: f,
                input: '@0@.bz2'.format(f),
                capture: true,
                build_by_default: true,
                command: [ bzip2, '-dc', '@INPUT0@' ],
                install: install_blobs,
                install_dir: config_host['qemu_datadir'])
endforeach

subdir('descriptors')

blobs = files(
  'QEMU,cgthree.bin',
  'QEMU,tcx.bin',
  'bamboo.dtb',
  'bios-256k.bin',
  'bios.bin',
  'canyonlands.dtb',
  'edk2-licenses.txt',
  'efi-e1000.rom',
  'efi-e1000e.rom',
  'efi-eepro100.rom',
  'efi-ne2k_pci.rom',
  'efi-pcnet.rom',
  'efi-rtl8139.rom',
  'efi-virtio.rom',
  'efi-vmxnet3.rom',
  'hppa-firmware.img',
  'kvmvapic.bin',
  'linuxboot.bin',
  'linuxboot_dma.bin',
  'multiboot.bin',
  'openbios-ppc',
  'openbios-sparc32',
  'openbios-sparc64',
  'opensbi-riscv32-virt-fw_jump.bin',
  'opensbi-riscv64-sifive_u-fw_jump.bin',
  'opensbi-riscv64-virt-fw_jump.bin',
  'palcode-clipper',
  'petalogix-ml605.dtb',
  'petalogix-s3adsp1800.dtb',
  'ppc_rom.bin',
  'pvh.bin',
  'pxe-e1000.rom',
  'pxe-eepro100.rom',
  'pxe-ne2k_pci.rom',
  'pxe-pcnet.rom',
  'pxe-rtl8139.rom',
  'pxe-virtio.rom',
  'qemu-nsis.bmp',
  'qemu_vga.ndrv',
  's390-ccw.img',
  's390-netboot.img',
  'sgabios.bin',
  'skiboot.lid',
  'slof.bin',
  'spapr-rtas.bin',
  'u-boot-sam460-20100605.bin',
  'u-boot.e500',
  'vgabios-ati.bin',
  'vgabios-bochs-display.bin',
  'vgabios-cirrus.bin',
  'vgabios-qxl.bin',
  'vgabios-ramfb.bin',
  'vgabios-stdvga.bin',
  'vgabios-virtio.bin',
  'vgabios-vmware.bin',
)

if install_blobs
  install_data(blobs, install_dir: config_host['qemu_datadir'])
endif
