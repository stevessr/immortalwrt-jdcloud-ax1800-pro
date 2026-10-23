#!/usr/bin/env python3
"""Execute first-boot defaults only inside a temporary, stubbed filesystem."""
import json
from pathlib import Path
import os
import subprocess
import tempfile

source = Path('package/custom/ax1800-pro-defaults/files/99-zz-ax1800-pro').read_text()
for legacy_sae_file in (False, True):
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
        if legacy_sae_file:
            (root / 'etc/sakura/sae-password').write_text('legacy-password\n')
        # Rewrite absolute paths solely in the test copy; never touch host /etc.
        test = source.replace('/lib/functions.sh', str(root / 'lib/functions.sh'))
        test = test.replace('/etc/', str(root / 'etc') + '/')
        test = test.replace('/usr/bin/fish', str(root / 'usr/bin/fish'))
        script = root / 'test.sh'
        script.write_text(test)
        env = dict(os.environ, PATH=str(root / 'bin') + ':' + os.environ['PATH'],
                   UCI_LOG=str(root / 'uci.log'))
        subprocess.run(['sh', str(script)], env=env, check=True)
        log = (root / 'uci.log').read_text()
        for iface in ('default_radio0', 'default_radio1'):
            assert f'wireless.{iface}.ssid=sakura' in log
            assert f'wireless.{iface}.encryption=none' in log
            assert f'wireless.{iface}.wps_pushbutton=0' in log
            assert f'wireless.{iface}.disabled=0' in log
            for old_option in ('key', 'sae_password_file', 'sae_pwe', 'ieee80211w', 'wpa_psk_file'):
                assert f'delete wireless.{iface}.{old_option}' in log
        for radio in ('radio0', 'radio1'):
            assert f'wireless.{radio}.disabled=0' in log
        assert 'encryption=sae' not in log
        assert 'sae_password_file=' not in log
        assert 'disabled=1' not in log
        assert str(root / 'usr/bin/fish') in (root / 'etc/passwd').read_text()
        if legacy_sae_file:
            assert (root / 'etc/sakura/sae-password').read_text() == 'legacy-password\n'
print('PASS: open AP defaults on both radios, legacy SAE file ignored; fish login')
