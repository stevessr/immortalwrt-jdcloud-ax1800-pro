#!/usr/bin/env python3
"""Execute first-boot defaults only inside a temporary, stubbed filesystem."""
from pathlib import Path
import os
import subprocess
import tempfile

source = Path('package/custom/ax1800-pro-defaults/files/99-zz-ax1800-pro').read_text()
for provisioned in (False, True):
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for d in ('etc/config', 'etc/sakura', 'usr/bin', 'lib', 'bin'):
            (root / d).mkdir(parents=True, exist_ok=True)
        (root / 'etc/config/wireless').touch()
        (root / 'etc/passwd').write_text('root:x:0:0:root:/root:/bin/ash\n')
        (root / 'usr/bin/fish').touch(mode=0o755)
        (root / 'lib/functions.sh').write_text('''
board_name() { echo jdcloud,re-ss-01; }
config_load() { :; }
config_get() { eval "$1=ap"; }
config_foreach() {
    case "$2" in
        wifi-iface) "$1" default_radio0; "$1" default_radio1;;
        wifi-device) "$1" radio0; "$1" radio1;;
    esac
}
''')
        (root / 'bin/uci').write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$UCI_LOG"\n')
        (root / 'bin/uci').chmod(0o755)
        if provisioned:
            (root / 'etc/sakura/sae-password').write_text('abcde\n')
        # Rewrite absolute paths solely in the test copy; never touch host /etc.
        test = source.replace('/lib/functions.sh', str(root / 'lib/functions.sh'))
        test = test.replace('/etc/', str(root / 'etc') + '/')
        test = test.replace('/usr/bin/fish', str(root / 'usr/bin/fish'))
        script = root / 'test.sh'
        script.write_text(test)
        env = dict(os.environ, PATH=str(root / 'bin') + ':' + os.environ['PATH'], UCI_LOG=str(root / 'uci.log'))
        subprocess.run(['sh', str(script)], env=env, check=True)
        log = (root / 'uci.log').read_text()
        for iface in ('default_radio0', 'default_radio1'):
            assert f'wireless.{iface}.ssid=sakura' in log
            assert f'wireless.{iface}.encryption=sae' in log
            assert f'wireless.{iface}.ieee80211w=2' in log
            assert f'delete wireless.{iface}.key' in log
            assert (f'wireless.{iface}.disabled=0' in log) == provisioned
        assert 'encryption=none' not in log
        assert str(root / 'usr/bin/fish') in (root / 'etc/passwd').read_text()
        if provisioned:
            assert (root / 'etc/sakura/sae-password').stat().st_mode & 0o777 == 0o600
print('PASS: provisioned SAE-only and unprovisioned disabled-AP defaults; fish login')
