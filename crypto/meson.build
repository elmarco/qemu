util_ss.add(files('aes.c'))
util_ss.add(files('init.c'))
if 'CONFIG_GCRYPT' in config_host
  util_ss.add(files('random-gcrypt.c'))
elif 'CONFIG_GNUTLS' in config_host
  util_ss.add(files('random-gnutls.c'), gnutls)
else
  util_ss.add(files('random-platform.c'))
endif
