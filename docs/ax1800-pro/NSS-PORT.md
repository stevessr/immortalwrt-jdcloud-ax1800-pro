# Scoped NSS port (not a replacement of the official source tree)

Base: official `immortalwrt/immortalwrt` master at
`e695009c15c623f4f6a83376b505faaf7a4ae5b5`.
Donor: `VIKINGYFY/immortalwrt` main at
`f9b0ce7650fdcc7f4793256a3ae43c1132e2bc49`.
Both use Linux 6.18.55. See `nss-provenance.json` for the imported paths.

The port includes the QSDK 13.1 NSS driver/ECM/dataplane/clients/SSDK,
Linux 6.18 compatibility hooks and skb recycler, ath11k/mac80211 NSS
patches and MU-EDCA hostapd interface, matching radio firmware,
IPQ6018 clock/memory/DTS support and the RE-SS-01 board DTS.
The conflicting upstream SSDK definition and two replaced IPQ6018
reserved-memory/clock patches are removed. Upstream mac80211 metadata
scanning and unrelated ath12k changes are retained.

Not imported: donor CPU OPP/speed-bin unlocks or CPR voltage tuning,
branding, feeds, general network defaults, unrelated
SoC targets, fullcone replacement, and mass changes to other board profiles.
Existing official PPE source remains, but this IPQ60xx configuration uses
NSS DP/SSDK instead. This branch validates ONLY `jdcloud_re-ss-01`; shared
IPQ60xx changes and the matching firmware package must not be assumed
compatible with other device images.

Original source licenses, patch authors and attribution are retained.
Imported code is not proof of a successful build or of runtime offload.
NSS fast paths can bypass TC/eBPF/transparent proxy/SQM processing. Those
services must be configured and verified deliberately, not all enabled
simultaneously. No proxy subscriptions or credentials are included.

## Integration fixes on top of the donor

- Explicitly disable the four retained official PPE Kconfig options when using
  NSS, so noninteractive kernel configuration has no unanswered prompts.
- ECM patch 016 restores support for the official conntrack notifier-chain API
  (`CONFIG_NF_CONNTRACK_CHAIN_EVENTS`), while retaining the non-chain API. It
  also unregisters callbacks when acquiring a netns reference fails. A host
  test compiles the actual patched callbacks against both API signatures and
  exercises dispatch, registration failure and reference cleanup. This keeps
  the official fullcone implementation rather than removing it to fit ECM.
