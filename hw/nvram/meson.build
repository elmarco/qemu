softmmu_ss.add(files(
  'chrp_nvram.c',
  'eeprom93xx.c',
  'fw_cfg.c',
))
softmmu_ss.add(when: 'CONFIG_AT24C', if_true: files('eeprom_at24c.c'))
softmmu_ss.add(when: 'CONFIG_DS1225Y', if_true: files('ds1225y.c'))
softmmu_ss.add(when: 'CONFIG_MAC_NVRAM', if_true: files('mac_nvram.c'))

specific_ss.add(when: 'CONFIG_PSERIES', if_true: files('spapr_nvram.c'))
specific_ss.add(when: 'CONFIG_NRF51_SOC', if_true: files('nrf51_nvm.c'))
