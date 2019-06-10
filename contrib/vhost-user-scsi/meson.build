if config_host.has_key('CONFIG_LIBISCSI')
  executable('vhost-user-scsi', files('vhost-user-scsi.c'),
             link_with: libvhost_user,
             dependencies: [qemuutil, libiscsi])
endif
