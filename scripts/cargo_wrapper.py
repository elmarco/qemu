#!/usr/bin/env python3

import glob
import os
import os.path
import shutil
import subprocess
import sys

command, meson_build_dir, meson_current_source_dir, meson_build_root, target, target_triple = sys.argv[
    1:7]

# avoid conflict with qemu "target" directory
cargo_target_dir = os.path.join(meson_build_dir, 'rs-target')

env = os.environ.copy()
env['CARGO_TARGET_DIR'] = cargo_target_dir
env['MESON_CURRENT_BUILD_DIR'] = meson_build_dir
env['MESON_BUILD_ROOT'] = meson_build_root

if command == 'build':
    # cargo build
    cargo_cmd = ['cargo', 'build', '--all-targets',
                 '--manifest-path', os.path.join(meson_current_source_dir, 'Cargo.toml')]
    if target_triple:
        cargo_cmd += ['--target', target_triple]
    if target == 'release':
        cargo_cmd.append('--release')
else:
    print("Unknown command:", command)
    sys.exit(1)

try:
    subprocess.run(cargo_cmd, env=env, check=True)
except subprocess.SubprocessError:
    sys.exit(1)

if command == 'build':
    # Copy files to build dir
    all_a = os.path.join(cargo_target_dir, target_triple, target, '*.a')
    for f in glob.glob(all_a):
        shutil.copy(f, meson_build_dir)
