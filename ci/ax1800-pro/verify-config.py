#!/usr/bin/env python3
"""Fail closed if Kconfig silently drops requested functionality."""
from pathlib import Path
import sys

def parse(path):
    values = {}
    for line in Path(path).read_text().splitlines():
        if line.startswith('CONFIG_') and '=' in line:
            key, value = line.split('=', 1)
            values[key] = value
        elif line.startswith('# CONFIG_') and line.endswith(' is not set'):
            values[line[2:-11]] = 'n'
    return values

seed = parse('ci/ax1800-pro/config.seed')
actual = parse('.config')
errors = []
for name, value in seed.items():
    if name == 'CONFIG_BPF_TOOLCHAIN_HOST_PATH':
        continue
    found = actual.get(name, 'n')
    if found != value:
        errors.append(f'{name}: requested {value}, got {found}')
if errors:
    sys.exit('\n'.join(errors))
print(f'PASS: {len(seed)} requested build settings retained')
