#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
python3 - <<'PY'
import json
from pathlib import Path
lock = json.loads(Path('ci/ax1800-pro/sources.lock.json').read_text())
expected = ''.join(f"src-git {f['name']} {f['url']}^{f['commit']}\n" for f in lock['feeds'])
assert Path('feeds.conf.default').read_text() == expected, 'Feed pins differ from lock'
PY
./scripts/feeds update -a
./scripts/feeds uninstall -a
# Install the image's dependency closure, not thousands of unrelated feed menus.
./scripts/feeds install -f -p passwall_packages \
    xray-core sing-box chinadns-ng geoview tcping v2ray-geoip v2ray-geosite
./scripts/feeds install \
    luci luci-ssl-openssl luci-compat luci-app-mentohust luci-app-openclash \
    luci-app-nikki-rs luci-app-passwall2 daed luci-app-daed daed-geoip daed-geosite \
    zerotier luci-app-zerotier cloudflared luci-app-ttyd mmc-utils \
    luci-app-statistics luci-app-sqm fish e2fsprogs f2fs-tools \
    automount cpufreq libpci libcap libudev-zero iperf3 luci-base
python3 - <<'PY'
import json, subprocess
from pathlib import Path
for f in json.loads(Path('ci/ax1800-pro/sources.lock.json').read_text())['feeds']:
    actual = subprocess.check_output(['git', '-C', 'feeds/' + f['name'], 'rev-parse', 'HEAD'], text=True).strip()
    assert actual == f['commit'], (f['name'], actual)
PY
cp ci/ax1800-pro/config.seed .config
# Local development may explicitly override the host LLVM prefix, never feed pins.
if [[ -n ${LOCAL_LLVM_PREFIX:-} ]]; then
    sed -i "s|^CONFIG_BPF_TOOLCHAIN_HOST_PATH=.*|CONFIG_BPF_TOOLCHAIN_HOST_PATH=\"${LOCAL_LLVM_PREFIX}\"|" .config
fi
make defconfig
python3 ci/ax1800-pro/verify-config.py
