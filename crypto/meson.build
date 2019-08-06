util_ss.add(files('aes.c'))
util_ss.add(files('init.c'))
if config_host.has_key('CONFIG_GCRYPT')
  util_ss.add(files('random-gcrypt.c'))
elif config_host.has_key('CONFIG_GNUTLS')
  util_ss.add(files('random-gnutls.c'), gnutls)
else
  util_ss.add(files('random-platform.c'))
endif

