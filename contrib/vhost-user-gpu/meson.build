if config_host.has_key('CONFIG_VIRGL') and config_host.has_key('CONFIG_GBM')
  executable('vhost-user-gpu', files('main.c', 'virgl.c', 'vugbm.c'),
             link_with: libvhost_user,
             dependencies: [qemuutil, pixman, gbm, virgl])
endif
