# JDCloud AX1800 Pro / RE-SS-01 build

This is an official ImmortalWrt fork plus the separately documented NSS port.
See `docs/ax1800-pro/NSS-PORT.md`. Only this device is a supported CI target.
Linux is pinned to the official base's **6.18.55** with the donor's matching
6.18 NSS adaptations. Package feeds and additional recipes are commit-pinned
in `sources.lock.json`; no floating personal firmware tree is checked out.

Run `bash ci/ax1800-pro/prepare.sh`, `make download -j8`, then `make -j4`.
CI uses Ubuntu 24.04, LLVM 18, standard GitHub-hosted runners and no secrets.
The workflow verifies requested Kconfig values, installed package manifest,
actual vmlinux BTF, FIT metadata and partition limits before uploading firmware.
A successful artifact means **built and checked**, not device-tested.

## Storage and migration limits

This customization is for the existing expanded layout: 16 MiB `0:HLOS`,
2 GiB `rootfs`, separate large `storage`. Only a sysupgrade tar is produced.
The root payload is 64 KiB aligned; no GPT, bootloader, ART/calibration or
storage image is generated or rewritten. This image is NOT suitable for an
unmodified stock-sized root partition or the small `rootfs_1` slot.
Before flashing, independently confirm active slot, GPT, hardware identity,
image hashes, kernel/root sizes, backup integrity and recovery access.
Do not restore all of QWRT's network/firewall configuration onto this image.

## Defaults and credentials

Both radios use SSID `sakura`, SAE-only WPA3-Personal and required PMF.
An external root-only `/etc/sakura/sae-password` is used rather than the
WPA2 PSK field, which requires a different password-length validation.
No Wi-Fi/admin password is present in source, Actions secrets, logs or images.
Wi-Fi stays disabled until a nonempty local provisioning file is installed.
Short SAE passwords may still be rejected by some client UIs; association
must be verified on the actual clients. The public image has normal OpenWrt
admin defaults: provision the router's existing root hash locally before use.
Root's login shell is fish. `/bin/sh` stays ash for system scripts. Use
`ssh root@router 'sh -c ...'` for POSIX shell automation after migration.

OpenClash includes the hash-verified official Mihomo arm64 core; Nikki-RS
includes its pinned clash-rs package. Passwall2 uses nftables, not legacy
iptables. Proxy applications, MentoHUST, ZeroTier, cloudflared and SQM are
installed but not automatically enabled or supplied with accounts/tunnels.
`daed` is included as requested; its upstream was archived in September 2026.
The older kcpufreq UI is included with LuCI compatibility and left disabled;
no unsupported CPU frequency is forced.

## NSS versus traffic inspection

NSS acceleration is present, including ath11k Wi-Fi offload, SSDK, ECM and
NSS qdisc support. Software/hardware fw4 flow offload is disabled to avoid
stacking separate accelerators. NSS fast paths and TC/eBPF/SQM/transparent
proxies are not assumed to coexist correctly. Before enabling an inspector
or transparent proxy, disable ECM and Wi-Fi NSS offload, reboot as necessary,
and verify that traffic actually reaches the requested hooks. Only then
consider selectively re-enabling acceleration. Installing all applications
is not equivalent to enabling all of them safely at once.

Additional recipe adaptations: iperf3's LuCI build include and duplicate
BuildPackage were corrected; kcpufreq declares its LuCI host tool and legacy
runtime dependencies. Original licenses/authors are retained.
