#!/usr/bin/env python3
"""Build evidence, NOT authorization to flash or proof that hardware boots."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

out = Path('bin/targets/qualcommax/ipq60xx')
images = list(out.glob('*jdcloud_re-ss-01-squashfs-sysupgrade.bin'))
assert len(images) == 1, images
image = images[0]
evidence = out / 'evidence'
evidence.mkdir(exist_ok=True)
result = {'image': image.name, 'sha256': hashlib.sha256(image.read_bytes()).hexdigest(),
          'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
          'status': 'build-verified-not-device-tested', 'partitions_written': ['0:HLOS', 'rootfs'],
          'gpt_changes': False}
with tarfile.open(image) as tf:
    regular = [m for m in tf.getmembers() if m.isfile()]
    assert len(regular) == 3, [m.name for m in regular]
    contents = {Path(m.name).name: m for m in regular}
    assert set(contents) == {'CONTROL', 'kernel', 'root'}, contents
    assert all(m.name.startswith('sysupgrade-') and '..' not in Path(m.name).parts for m in regular)
    assert 0 < contents['kernel'].size <= 16 * 1024 * 1024
    assert 0 < contents['root'].size <= (2048 - 64) * 1024 * 1024
    assert contents['root'].size % 65536 == 0, 'Root must be 64 KiB aligned for QWRT migration'
    kernel = tf.extractfile(contents['kernel']).read()
    assert kernel[:4] == bytes.fromhex('d00dfeed'), 'Kernel is not FIT'
    root = tf.extractfile(contents['root'])
    assert root.read(4) == b'hsqs', 'Root is not SquashFS'
    result['kernel_bytes'] = len(kernel)
    result['root_bytes'] = contents['root'].size
    fit = evidence / 'kernel.itb'
    fit.write_bytes(kernel)
    fit_listing = subprocess.check_output(['dumpimage', '-l', str(fit)], text=True)
    assert 'config@cp03-c2' in fit_listing, fit_listing
    (evidence / 'fit.txt').write_text(fit_listing)
    fit.unlink()
metadata = evidence / 'image-metadata.json'
subprocess.run(['staging_dir/host/bin/fwtool', '-i', str(metadata), str(image)], check=True)
meta = json.loads(metadata.read_text())
assert 'jdcloud,re-ss-01' in meta['supported_devices'], meta
assert 'jdcloud,ax1800-pro' in meta['supported_devices'], meta

manifests = list(out.glob('*jdcloud_re-ss-01*.manifest'))
assert len(manifests) == 1, manifests
installed = {line.split()[0] for line in manifests[0].read_text().splitlines() if line.strip()}
available = {line[9:] for line in Path('tmp/.packageinfo').read_text().splitlines() if line.startswith('Package: ')}
requested = {line[15:-2] for line in Path('ci/ax1800-pro/config.seed').read_text().splitlines()
             if line.startswith('CONFIG_PACKAGE_') and line.endswith('=y')}
required = requested & available
assert not (required - installed), 'Missing packages: ' + repr(sorted(required - installed))
assert not (installed & {'firewall', 'iptables-zz-legacy', 'dnsmasq'}), installed
result['verified_packages'] = sorted(required)

kernels = list(Path('build_dir').glob('target-*/linux-qualcommax_ipq60xx/linux-6.18.*/.config'))
assert len(kernels) == 1, kernels
kconfig = kernels[0]
config = dict(line.split('=', 1) for line in kconfig.read_text().splitlines() if line.startswith('CONFIG_') and '=' in line)
for name in ['BPF', 'BPF_SYSCALL', 'BPF_JIT', 'DEBUG_INFO_BTF', 'DEBUG_INFO_BTF_MODULES',
             'BPF_EVENTS', 'CGROUP_BPF', 'KPROBES', 'IKCONFIG_PROC', 'NET_CLS_ACT']:
    assert config.get('CONFIG_' + name) == 'y', (name, config.get('CONFIG_' + name))
for name in ['NET_CLS_BPF', 'NET_ACT_BPF', 'NET_SCH_INGRESS', 'TUN', 'NFT_TPROXY']:
    assert config.get('CONFIG_' + name) in ('y', 'm'), (name, config.get('CONFIG_' + name))
vmlinux = kconfig.parent / 'vmlinux'
sections = subprocess.check_output(['readelf', '-SW', str(vmlinux)], text=True)
assert '.BTF ' in sections, 'Missing actual vmlinux BTF section'
(evidence / 'vmlinux-sections.txt').write_text(sections)
shutil.copyfile(kconfig, evidence / 'kernel.config')
shutil.copyfile('.config', evidence / 'build.config')
shutil.copyfile('ci/ax1800-pro/sources.lock.json', evidence / 'sources.lock.json')
shutil.copyfile('docs/ax1800-pro/nss-provenance.json', evidence / 'nss-provenance.json')
roots = list(Path('build_dir').glob('target-*/root-qualcommax'))
assert len(roots) == 1, roots
for name in ['usr/bin/fish', 'etc/openclash/core/clash_meta', 'usr/bin/clash-rs', 'usr/bin/fastfetch']:
    assert (roots[0] / name).is_file(), 'Missing binary: ' + name
assert not (roots[0] / 'etc/sakura/sae-password').exists(), 'Credentials must not be baked into public images'
(evidence / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
