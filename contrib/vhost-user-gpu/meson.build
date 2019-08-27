if 'CONFIG_VIRGL' in config_host and 'CONFIG_GBM' in config_host
  executable('vhost-user-gpu', files('main.c', 'virgl.c', 'vugbm.c'),
             link_with: libvhost_user,
             dependencies: [qemuutil, pixman, gbm, virgl])
endif
