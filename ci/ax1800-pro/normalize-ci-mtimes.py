#!/usr/bin/env python3
"""Stable checkout mtimes for exact-input, immutable CI compiler caches only.

OpenWrt preparation stamps hash input mtimes, not just their contents. A fresh
checkout otherwise invalidates a restored compiler even if its input hash is
identical. Compiler caches must have exact content-based keys, no fallback keys.
Generated files and build outputs are never touched. Git commit dates (and thus
SOURCE_DATE_EPOCH) are unchanged. Never run this in a developer worktree.
"""
import os
from pathlib import Path
import subprocess

assert os.environ.get('GITHUB_ACTIONS') == 'true', 'CI-only timestamp normalization'
epoch = 946684800  # 2000-01-01 UTC, before all generated build stamps
repos = [Path('.')]
if Path('feeds').is_dir():
    repos += sorted(p for p in Path('feeds').iterdir() if (p / '.git').exists())
count = 0
for repo in repos:
    names = subprocess.check_output(['git', '-C', str(repo), 'ls-files', '-z']).split(b'\0')
    for raw in filter(None, names):
        path = repo / os.fsdecode(raw)
        if path.is_dir():
            continue  # No recursion through a gitlink.
        os.utime(path, (epoch, epoch), follow_symlinks=False)
        count += 1
print(f'Normalized {count} tracked source mtimes in {len(repos)} immutable checkouts')
