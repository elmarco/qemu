# usb subsystem core
softmmu_ss.add(files(
  'bus.c',
  'combined-packet.c',
  'core.c',
  'libhw.c'
))

softmmu_ss.add(when: 'CONFIG_USB', if_true: files(
  'desc.c',
  'desc-msos.c',
))

# usb host adapters
softmmu_ss.add(when: 'CONFIG_USB_UHCI', if_true: files('hcd-uhci.c'))
softmmu_ss.add(when: 'CONFIG_USB_OHCI', if_true: files('hcd-ohci.c'))
softmmu_ss.add(when: 'CONFIG_USB_OHCI_PCI', if_true: files('hcd-ohci-pci.c'))
softmmu_ss.add(when: 'CONFIG_USB_EHCI', if_true: files('hcd-ehci.c'))
softmmu_ss.add(when: 'CONFIG_USB_EHCI_PCI', if_true: files('hcd-ehci-pci.c'))
softmmu_ss.add(when: 'CONFIG_USB_EHCI_SYSBUS', if_true: files('hcd-ehci.c', 'hcd-ehci-sysbus.c'))
softmmu_ss.add(when: 'CONFIG_USB_XHCI', if_true: files('hcd-xhci.c'))
softmmu_ss.add(when: 'CONFIG_USB_XHCI_NEC', if_true: files('hcd-xhci-nec.c'))
softmmu_ss.add(when: 'CONFIG_USB_MUSB', if_true: files('hcd-musb.c'))

specific_ss.add(when: 'CONFIG_TUSB6010', if_true: files('tusb6010.c'))
specific_ss.add(when: 'CONFIG_IMX', if_true: files('chipidea.c'))

# emulated usb devices
softmmu_ss.add(when: 'CONFIG_USB', if_true: files('dev-hub.c'))
softmmu_ss.add(when: 'CONFIG_USB', if_true: files('dev-hid.c'))
softmmu_ss.add(when: 'CONFIG_USB_TABLET_WACOM', if_true: files('dev-wacom.c'))
softmmu_ss.add(when: 'CONFIG_USB_STORAGE_BOT', if_true: files('dev-storage.c'))
softmmu_ss.add(when: 'CONFIG_USB_STORAGE_UAS', if_true: files('dev-uas.c'))
softmmu_ss.add(when: 'CONFIG_USB_AUDIO', if_true: files('dev-audio.c'))
softmmu_ss.add(when: 'CONFIG_USB_SERIAL', if_true: files('dev-serial.c'))
softmmu_ss.add(when: 'CONFIG_USB_NETWORK', if_true: files('dev-network.c'))
softmmu_ss.add(when: 'CONFIG_USB_BLUETOOTH', if_true: files('dev-bluetooth.c'))

softmmu_ss.add(when: 'CONFIG_USB_SMARTCARD', if_true: files('dev-smartcard-reader.c'))
softmmu_ss.add(when: ['CONFIG_USB_SMARTCARD', 'CONFIG_SMARTCARD', cacard], if_true: files(
  'ccid-card-emulated.c',
  'ccid-card-passthru.c',
))

softmmu_ss.add(when: ['CONFIG_POSIX', 'CONFIG_USB_STORAGE_MTP'], if_true: files('dev-mtp.c'))

# usb redirect
softmmu_ss.add(when: [usbredir, 'CONFIG_USB_REDIR'], if_true: files('redirect.c', 'quirks.c'))

# usb pass-through
softmmu_ss.add(when: [libusb, 'CONFIG_USB'], if_true: files('host-libusb.c'), if_false: files('host-stub.c'))
softmmu_ss.add(when: 'CONFIG_ALL', if_true: files('host-stub.c'))

softmmu_ss.add(when: [libusb, 'CONFIG_XEN'], if_true: files('xen-usb.c'))
