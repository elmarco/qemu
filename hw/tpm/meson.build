softmmu_ss.add(when: 'CONFIG_TPM', if_true: files('tpm_util.c'))
softmmu_ss.add(when: 'CONFIG_TPM_TIS', if_true: files('tpm_tis.c'))
softmmu_ss.add(when: 'CONFIG_TPM_CRB', if_true: files('tpm_crb.c'))
softmmu_ss.add(when: 'CONFIG_TPM_PASSTHROUGH', if_true: files('tpm_passthrough.c'))
softmmu_ss.add(when: 'CONFIG_TPM_EMULATOR', if_true: files('tpm_emulator.c'))

specific_ss.add(when: ['CONFIG_SOFTMMU', 'CONFIG_TPMDEV'], if_true: files('tpm_ppi.c'))
