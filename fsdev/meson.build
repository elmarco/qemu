if have_tools and libattr.found() and libcap.found() and 'CONFIG_VIRTFS' in config_host and 'CONFIG_ATTR' in config_host
  executable('virtfs-proxy-helper', files('virtfs-proxy-helper.c', '9p-marshal.c', '9p-iov-marshal.c'),
             dependencies: [qemuutil, libattr, libcap])
endif
