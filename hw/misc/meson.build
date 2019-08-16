softmmu_ss.add(when: 'CONFIG_APPLESMC', if_true: files('applesmc.c'))
softmmu_ss.add(when: 'CONFIG_EDU', if_true: files('edu.c'))
softmmu_ss.add(when: 'CONFIG_FW_CFG_DMA', if_true: files('vmcoreinfo.c'))
softmmu_ss.add(when: 'CONFIG_ISA_DEBUG', if_true: files('debugexit.c'))
softmmu_ss.add(when: 'CONFIG_ISA_TESTDEV', if_true: files('pc-testdev.c'))
softmmu_ss.add(when: 'CONFIG_MAX111X', if_true: files('max111x.c'))
softmmu_ss.add(when: 'CONFIG_PCA9552', if_true: files('pca9552.c'))
softmmu_ss.add(when: 'CONFIG_PCI_TESTDEV', if_true: files('pci-testdev.c'))
softmmu_ss.add(when: 'CONFIG_SGA', if_true: files('sga.c'))
softmmu_ss.add(when: 'CONFIG_TMP105', if_true: files('tmp105.c'))
softmmu_ss.add(when: 'CONFIG_TMP421', if_true: files('tmp421.c'))
softmmu_ss.add(when: 'CONFIG_UNIMP', if_true: files('unimp.c'))

# ARM devices
softmmu_ss.add(when: 'CONFIG_PL310', if_true: files('arm_l2x0.c'))
softmmu_ss.add(when: 'CONFIG_INTEGRATOR_DEBUG', if_true: files('arm_integrator_debug.c'))
softmmu_ss.add(when: 'CONFIG_A9SCU', if_true: files('a9scu.c'))
softmmu_ss.add(when: 'CONFIG_ARM11SCU', if_true: files('arm11scu.c'))

# Mac devices
softmmu_ss.add(when: 'CONFIG_MOS6522', if_true: files('mos6522.c'))

# PKUnity SoC devices
softmmu_ss.add(when: 'CONFIG_PUV3', if_true: files('puv3_pm.c'))

subdir('macio')

specific_ss.add(when: 'CONFIG_IVSHMEM_DEVICE', if_true: files('ivshmem.c'))

specific_ss.add(when: 'CONFIG_REALVIEW', if_true: files('arm_sysctl.c'))
specific_ss.add(when: 'CONFIG_NSERIES', if_true: files('cbus.c'))
specific_ss.add(when: 'CONFIG_ECCMEMCTL', if_true: files('eccmemctl.c'))
specific_ss.add(when: 'CONFIG_EXYNOS4', if_true: files('exynos4210_pmu.c', 'exynos4210_clk.c', 'exynos4210_rng.c'))
specific_ss.add(when: 'CONFIG_IMX', if_true: files(
  'imx25_ccm.c',
  'imx2_wdt.c',
  'imx31_ccm.c',
  'imx6_ccm.c',
  'imx6_src.c',
  'imx6ul_ccm.c',
  'imx7_ccm.c',
  'imx7_gpr.c',
  'imx7_snvs.c',
  'imx_ccm.c',
))
specific_ss.add(when: 'CONFIG_MILKYMIST', if_true: files('milkymist-hpdmc.c', 'milkymist-pfpu.c'))
specific_ss.add(when: 'CONFIG_MAINSTONE', if_true: files('mst_fpga.c'))
specific_ss.add(when: 'CONFIG_OMAP', if_true: files(
  'omap_clk.c',
  'omap_gpmc.c',
  'omap_l4.c',
  'omap_sdrc.c',
  'omap_tap.c',
))
specific_ss.add(when: 'CONFIG_RASPI', if_true: files('bcm2835_mbox.c', 'bcm2835_property.c', 'bcm2835_rng.c'))
specific_ss.add(when: 'CONFIG_SLAVIO', if_true: files('slavio_misc.c'))
specific_ss.add(when: 'CONFIG_ZYNQ', if_true: files('zynq_slcr.c', 'zynq-xadc.c'))
specific_ss.add(when: 'CONFIG_STM32F2XX_SYSCFG', if_true: files('stm32f2xx_syscfg.c'))
specific_ss.add(when: 'CONFIG_MIPS_CPS', if_true: files('mips_cmgcr.c', 'mips_cpc.c'))
specific_ss.add(when: 'CONFIG_MIPS_ITU', if_true: files('mips_itu.c'))
specific_ss.add(when: 'CONFIG_MPS2_FPGAIO', if_true: files('mps2-fpgaio.c'))
specific_ss.add(when: 'CONFIG_MPS2_SCC', if_true: files('mps2-scc.c'))

specific_ss.add(when: 'CONFIG_TZ_MPC', if_true: files('tz-mpc.c'))
specific_ss.add(when: 'CONFIG_TZ_MSC', if_true: files('tz-msc.c'))
specific_ss.add(when: 'CONFIG_TZ_PPC', if_true: files('tz-ppc.c'))
specific_ss.add(when: 'CONFIG_IOTKIT_SECCTL', if_true: files('iotkit-secctl.c'))
specific_ss.add(when: 'CONFIG_IOTKIT_SYSCTL', if_true: files('iotkit-sysctl.c'))
specific_ss.add(when: 'CONFIG_IOTKIT_SYSINFO', if_true: files('iotkit-sysinfo.c'))
specific_ss.add(when: 'CONFIG_ARMSSE_CPUID', if_true: files('armsse-cpuid.c'))
specific_ss.add(when: 'CONFIG_ARMSSE_MHU', if_true: files('armsse-mhu.c'))

specific_ss.add(when: 'CONFIG_PVPANIC', if_true: files('pvpanic.c'))
specific_ss.add(when: 'CONFIG_AUX', if_true: files('auxbus.c'))
specific_ss.add(when: 'CONFIG_ASPEED_SOC', if_true: files('aspeed_scu.c', 'aspeed_sdmc.c', 'aspeed_xdma.c'))
specific_ss.add(when: 'CONFIG_MSF2', if_true: files('msf2-sysreg.c'))
specific_ss.add(when: 'CONFIG_NRF51_SOC', if_true: files('nrf51_rng.c'))

specific_ss.add(when: 'CONFIG_GRLIB', if_true: files('grlib_ahb_apb_pnp.c'))
