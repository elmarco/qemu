if config_host.has_key('CONFIG_PVRDMA')
  # if not found, CONFIG_PVRDMA should not be set
  libumad = cc.find_library('ibumad', required: true)
  executable('rdmacm-mux', files('main.c'),
             dependencies: [glib, libumad])
endif
