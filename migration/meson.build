migration_files = files(
  'page_cache.c',
  'xbzrle.c',
  'vmstate-types.c',
  'vmstate.c',
  'qemu-file-channel.c',
  'qemu-file.c',
  'qjson.c',
)

if have_system
  libmigration = static_library('libmigration', sources: migration_files,
                                dependencies: [zlib, qom, io])
  migration = declare_dependency(link_with: libmigration)
  softmmu_ss.add(migration)
endif

softmmu_ss.add(files(
  'block-dirty-bitmap.c',
  'channel.c',
  'colo-failover.c',
  'colo.c',
  'exec.c',
  'fd.c',
  'global_state.c',
  'migration.c',
  'postcopy-ram.c',
  'savevm.c',
  'socket.c',
  'tls.c',
))

softmmu_ss.add(when: ['CONFIG_RDMA', rdma], if_true: files('rdma.c'))
softmmu_ss.add(when: 'CONFIG_LIVE_BLOCK_MIGRATION', if_true: files('block.c'))

specific_ss.add(when: 'CONFIG_SOFTMMU', if_true: [files('ram.c'), libpmem])
