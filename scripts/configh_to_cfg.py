#!/usr/bin/env python3
# Copyright (c) 2020 Red Hat, Inc.
#
# Author:
#  Marc-André Lureau <marcandre.lureau@redhat.com>
#
# This work is licensed under the terms of the GNU GPL, version 2 or
# later.  See the COPYING file in the top-level directory.

import argparse
from typing import List


def cfg_name(name: str) -> str:
    if name.startswith("CONFIG_") or name.startswith("TARGET_"):
        # drop the CONFIG_ prefix?
        return name
    return ""


def generate_cfg(header: str) -> List[str]:
    with open(header, encoding="utf-8") as cfg:
        config = [l.split()[1:] for l in cfg if l.startswith("#define")]

    cfg_list = []
    for c in config:
        name = cfg_name(c[0])
        if not name:
            continue
        if len(c) >= 2 and c[1] != "1":
            continue
        cfg_list.append("--cfg")
        cfg_list.append(name)
    return cfg_list


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("HEADER")
    args = parser.parse_args()
    print(" ".join(generate_cfg(args.HEADER)))


if __name__ == "__main__":
    main()
