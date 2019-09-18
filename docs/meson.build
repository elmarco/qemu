configure_file(output: 'version.texi',
               input: 'version.texi.in',
               configuration: config_host)

sphinx = find_program('sphinx-build', required: build_docs)

if sphinx.found()
  devel_rst = [
    'devel/decodetree.rst',
    'devel/index.rst',
    'devel/kconfig.rst',
    'devel/loads-stores.rst',
    'devel/memory.rst',
    'devel/migration.rst',
    'devel/secure-coding-practices.rst',
    'devel/stable-process.rst',
    'devel/tcg.rst',
    'devel/testing.rst',
  ]
  devel = custom_target('sphinx-devel',
                build_by_default: build_docs,
                input: devel_rst,
                depend_files: [files('conf.py', 'devel/conf.py')],
                output: 'devel',
                command: [sphinx, '-W', '-n', '-b', 'html', '-q',
                          '-Dversion=' + config_host['VERSION'],
                          '-Drelease=' + config_host['PKGVERSION'],
                          meson.current_source_dir() / 'devel',
                          '@OUTPUT@',
                         ])

  interop_rst = [
    'interop/bitmaps.rst',
    'interop/index.rst',
    'interop/live-block-operations.rst',
    'interop/pr-helper.rst',
    'interop/vhost-user-gpu.rst',
    'interop/vhost-user.rst',
  ]
  interop = custom_target('sphinx-interop',
                build_by_default: build_docs,
                input: interop_rst,
                depend_files: [files('conf.py', 'interop/conf.py')],
                output: 'interop',
                command: [sphinx, '-W', '-n', '-b', 'html', '-q',
                          '-Dversion=' + config_host['VERSION'],
                          '-Drelease=' + config_host['PKGVERSION'],
                          meson.current_source_dir() / 'interop',
                          '@OUTPUT@',
                         ])
  if build_docs
    install_subdir(meson.current_build_dir() / 'interop',
                   install_dir: config_host['qemu_docdir'],
                   exclude_directories: '.doctrees')
  endif

  specs_rst = [
    'specs/index.rst',
    'specs/ppc-spapr-xive.rst',
    'specs/ppc-xive.rst',
  ]
  specs = custom_target('sphinx-specs',
                build_by_default: build_docs,
                input: specs_rst,
                depend_files: [files('conf.py', 'specs/conf.py')],
                output: 'specs',
                command: [sphinx, '-W', '-n', '-b', 'html', '-q',
                          '-Dversion=' + config_host['VERSION'],
                          '-Drelease=' + config_host['PKGVERSION'],
                          meson.current_source_dir() / 'specs',
                          '@OUTPUT@',
                         ])
  if build_docs
    install_subdir(meson.current_build_dir() / 'specs',
                   install_dir: config_host['qemu_docdir'],
                   exclude_directories: '.doctrees')
  endif

  sphinxdocs = alias_target('sphinxdocs', devel, interop, specs)
endif
