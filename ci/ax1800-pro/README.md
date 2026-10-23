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

Both radios broadcast SSID `sakura` as **open, unencrypted Wi-Fi** on first
boot. No password or SAE provisioning file is required; the defaults explicitly
remove legacy WPA3/PSK settings and enable both radios. A leftover
`/etc/sakura/sae-password` file from an older image is ignored.
Anyone in range can connect and potentially access the bridged LAN and router
management services. Wi-Fi traffic is not protected by link-layer encryption.
Set a strong router admin password and enable WPA2/WPA3 before using this image
on an untrusted network. The public image contains no admin credentials; the
usual OpenWrt initial admin state still applies.
Root's login shell is fish. `/bin/sh` stays ash for system scripts. Use
`ssh root@router 'sh -c ...'` for POSIX shell automation after migration.

OpenClash includes the hash-verified official Mihomo arm64 core; Nikki-RS
includes its pinned clash-rs package. Passwall2 uses nftables, not legacy
iptables. Proxy applications, MentoHUST, ZeroTier, cloudflared, SQM, `bottom` and
`btop` are installed without accounts/tunnels. The first-boot defaults no
longer force UCI enabled switches to zero or remove init autostart symlinks.
Package defaults and later user choices are respected. Avoid running
competing transparent proxy stacks simultaneously.
GWRT is the default LuCI theme selected in Actions; `ubus`/`ubusd`, the
Cloudflared LuCI app and LuCI File Manager are included. `daed` is included as
requested; its upstream was archived in September 2026. The older kcpufreq UI
is included with LuCI compatibility; no unsupported CPU
frequency is forced.

## Recover an already-flashed image

Previous builds ran a one-shot `99-zz-ax1800-pro` script which disabled
init autostart for OpenClash, Nikki-RS, PassWall2, daed, MentoHUST,
ZeroTier, cloudflared, kcpufreq and SQM, and set several proxy UCI switches
to zero. Updating this source does not retroactively revert existing
device settings. Restore only the services you want to use. For daed and
MentoHUST, after filling in the required account/credential settings:

```sh
uci set daed.config.enabled='1'
uci set mentohust.config.enable='1'
uci commit daed
uci commit mentohust
/etc/init.d/daed enable
/etc/init.d/mentohust enable
# If not already running, start each wanted service:
/etc/init.d/daed start
/etc/init.d/mentohust start
```

The `/etc/uci-defaults/` script is normally removed after successful first
boot; do not run it manually. Enabling startup alone does not start a service
immediately, and changing a UCI switch alone does not guarantee a running
process. Check `/etc/init.d/<name> status` and `ubus call service list`
on the actual device. Never blindly enable every transparent proxy.

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

# Build integration notes

Pinned feeds receive only the tracked patches under `feed-patches/`. The fish
patch uses `TARGET_CC_NOCACHE` for Cargo's linker: Cargo needs one executable,
not the shell command `ccache aarch64-openwrt-linux-musl-gcc`. C compilation
can still use ccache. Feed commits remain pinned and patch drift is rejected.
The Actions seed explicitly selects `CONFIG_USE_APK=y`; MentoHUST core and
LuCI packages are built by this APK-enabled buildroot and their `.apk`
artifacts are verified. GWRT is pinned at
`c141330a519fc4bc342f484f6d938b03ec52d6c7`; Actions installs only
`luci-theme-gwrt` from that feed, not the upstream configuration fragment.
Valid UTF-8 MentoHUST server messages pass through; other server text is
converted from GBK to UTF-8 before printing and notification.

The pinned Nikki-RS feed uses prebuilt clash-rs 0.20.0-alpha. Its Hysteria2
configuration requires a `skip-cert-verify` boolean even when an upstream
Mihomo subscription omits the field. The tracked nikki_rs feed patch adds
`skip-cert-verify: false` only to Hysteria2 nodes missing that field, after
Nikki-RS assembles its run profile. Explicit settings remain unchanged and
TLS certificate verification remains enabled by default. The generated
`/etc/nikki-rs/run/config.yaml` is overwritten on restart; existing
devices need to install the same init-script normalization or correct the
source subscription/profile rather than only editing the generated file.


`kmod-qca-nss-drv-qdisc` links against the core driver's `nss_igs_*` exports,
so `kmod-qca-nss-drv-igs` and `NSS_DRV_IGS_ENABLE` stay enabled in
`config.seed`; the driver package otherwise force-disables IGS when its
package is absent and modpost would fail on undefined symbols.

CI normalizes only tracked source mtimes, since OpenWrt preparation stamps hash
mtimes. Compiler caches use exact content-based keys with no fallback. Generated
files and outputs are not timestamp-normalized. The completed Rust installation
and its build stamps are cached independently of firmware success; downloads and
ccache are saved on package failures too. A cache is never image/boot validation.
