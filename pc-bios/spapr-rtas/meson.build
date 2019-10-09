cc = meson.get_compiler('c').cmd_array().get(-1)
objcopy = find_program('objcopy')

spapr_rtas_o = custom_target(
  'spapr-rtas.o',
  output: 'spapr-rtas.o',
  input: 'spapr-rtas.S',
  command: [cc, '-mbig', '-c', '-o', '@OUTPUT@', '@INPUT@'],
)

spapr_rtas_img = custom_target(
  'spapr-rtas.img',
  output: 'spapr-rtas.img',
  input: spapr_rtas_o,
  command: [cc, '-nostdlib', '-mbig', '-o', '@OUTPUT@', '@INPUT@'],
)

custom_target(
  'spapr-rtas.bin',
  output: 'spapr-rtas.bin',
  input: spapr_rtas_img,
  command: [objcopy, '-O', 'binary', '-j', '.text', '@INPUT@', '@OUTPUT@'],
  build_by_default: true,
)
