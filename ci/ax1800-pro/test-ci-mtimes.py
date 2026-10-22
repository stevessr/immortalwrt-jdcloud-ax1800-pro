#!/usr/bin/env python3
import os
from pathlib import Path
import subprocess
import tempfile

script = Path(__file__).with_name('normalize-ci-mtimes.py').resolve()
with tempfile.TemporaryDirectory(prefix='ci-mtime-test-') as tmp:
    root = Path(tmp)
    subprocess.run(['git', 'init', '-q', str(root)], check=True)
    tracked = root / 'tracked'
    generated = root / 'generated'
    tracked.write_text('immutable source\n')
    generated.write_text('do not touch build outputs\n')
    (root / 'link').symlink_to('generated')
    subprocess.run(['git', '-C', str(root), 'add', 'tracked', 'link'], check=True)
    before = generated.stat().st_mtime_ns
    env = {**os.environ, 'GITHUB_ACTIONS': 'true'}
    subprocess.run(['python3', str(script)], cwd=root, env=env, check=True)
    assert tracked.stat().st_mtime == 946684800
    assert (root / 'link').lstat().st_mtime == 946684800
    assert generated.stat().st_mtime_ns == before
    assert tracked.read_text() == 'immutable source\n'
print('PASS: source mtime normalization never touches generated/symlink-target content')
