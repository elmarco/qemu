# common options
tracetool = [
  find_program('scripts/tracetool.py'),
   '--backend=' + config_host['TRACE_BACKENDS']
]

trace_events_files = []
foreach dir : [ '.' ] + trace_events_subdirs
  trace_events_file = meson.source_root() / dir / 'trace-events'
  trace_events_files += [ trace_events_file ]
  group_name = dir == '.' ? 'root' : dir.underscorify()
  group = '--group=' + group_name
  fmt = '@0@-' + group_name + '.@1@'

  trace_h = custom_target(fmt.format('trace', 'h'),
                          output: fmt.format('trace', 'h'),
                          input: trace_events_file,
                          command: [ tracetool, group, '--format=h', '@INPUT@' ],
                          capture: true)
  trace_c = custom_target(fmt.format('trace', 'c'),
                          output: fmt.format('trace', 'c'),
                          input: trace_events_file,
                          command: [ tracetool, group, '--format=c', '@INPUT@' ],
                          capture: true)
  if config_host.has_key('CONFIG_TRACE_UST')
    trace_ust_h = custom_target(fmt.format('trace-ust', 'h'),
                                output: fmt.format('trace-ust', 'h'),
                                input: trace_events_file,
                                command: [ tracetool, group, '--format=ust-events-h', '@INPUT@' ],
                                capture: true)
  endif
  trace_ss.add(trace_h, trace_c)
  if config_host.has_key('CONFIG_TRACE_DTRACE')
    trace_dtrace = custom_target(fmt.format('trace-dtrace', 'dtrace'),
                                 output: fmt.format('trace-dtrace', 'dtrace'),
                                 input: trace_events_file,
                                 command: [ tracetool, group, '--format=d', '@INPUT@' ],
                                 capture: true)
    trace_dtrace_h = custom_target(fmt.format('trace-dtrace', 'h'),
                                   output: fmt.format('trace-dtrace', 'h'),
                                   input: trace_dtrace,
                                   command: [ 'dtrace', '-o', '@OUTPUT@', '-h', '-s', '@INPUT@' ])
    trace_dtrace_o = custom_target(fmt.format('trace-dtrace', 'o'),
                                   output: fmt.format('trace-dtrace', 'o'),
                                   input: trace_dtrace,
                                   command: [ 'dtrace', '-o', '@OUTPUT@', '-G', '-s', '@INPUT@' ])

    trace_ss.add(trace_dtrace_h, trace_dtrace_o)
  endif
endforeach

custom_target('trace-events-all',
              output: 'trace-events-all',
              input: trace_events_files,
              command: [ 'cat', '@INPUT@' ],
              capture: true,
              install: true,
              install_dir: config_host['qemu_datadir'])

if config_host.has_key('CONFIG_TRACE_UST')
  trace_ust_all_h = custom_target(fmt.format('trace-ust', 'h'),
                                  output: fmt.format('trace-ust', 'h'),
                                  input: trace_events_files,
                                  command: [ tracetool, '--group=all', '--format=ust-events-h', '@INPUT@' ],
                                  capture: true)
  trace_ust_all_c = custom_target(fmt.format('trace-ust', 'c'),
                                  output: fmt.format('trace-ust', 'c'),
                                  input: trace_events_files,
                                  command: [ tracetool, '--group=all', '--format=ust-events-c', '@INPUT@' ],
                                  capture: true)
  trace_ss.add(trace_ust_all_h, trace_ust_all_c)
endif

trace_ss.add(when: 'CONFIG_TRACE_SIMPLE', if_true: files('simple.c'))
trace_ss.add(when: 'CONFIG_TRACE_FTRACE', if_true: files('ftrace.c'))
trace_ss.add(files('control.c'))
trace_ss.add(files('qmp.c'))
