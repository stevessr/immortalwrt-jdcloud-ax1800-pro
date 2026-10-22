#!/usr/bin/env python3
"""Compile actual patched ECM callbacks against both conntrack API shapes.

Checks notifier types, registration errors and netns failure cleanup. This is a
focused host test, not a substitute for compiling/loading the kernel module.
"""
from pathlib import Path
import subprocess
import tempfile

root = Path(__file__).resolve().parents[2]
with tempfile.TemporaryDirectory(prefix='ecm-api-test-') as tmp:
    tmp = Path(tmp)
    archive = root / 'dl/qca-nss-ecm-13.1.2026.04.03~8c7355b.tar.zst'
    subprocess.run(['tar', '--zstd', '-xf', str(archive), '-C', str(tmp)], check=True)
    source = next(tmp.glob('qca-nss-ecm-*'))
    for patch in sorted((root / 'package/qca-nss/qca-nss-ecm/patches').glob('*.patch')):
        subprocess.run(['patch', '-s', '-p1', '-d', str(source)], input=patch.read_bytes(), check=True)
    text = (source / 'ecm_conntrack_notifier.c').read_text()
    text = text.split('EXPORT_SYMBOL(ecm_conntrack_ipv4_event);', 1)[1]
    text = text.split('EXPORT_SYMBOL(ecm_conntrack_notifier_exit);', 1)[0]
    prefix = r'''
#include <assert.h>
#include <stdint.h>
#include <stddef.h>
#define CONFIG_NF_CONNTRACK_EVENTS 1
#define ECM_IPV6_ENABLE 1
#define LINUX_VERSION_CODE 0x061200
#define KERNEL_VERSION(a,b,c) (((a)<<16)|((b)<<8)|(c))
#define NOTIFY_DONE 0
#define AF_INET 2
#define AF_INET6 10
#define NFPROTO_IPV4 AF_INET
#define NFPROTO_IPV6 AF_INET6
#define S_IRUGO 0444
#define S_IWUSR 0200
#define EXPORT_SYMBOL(x)
#define DEBUG_INFO(...) ((void)0)
#define DEBUG_WARN(...) ((void)0)
#define DEBUG_ERROR(...) ((void)0)
#define DEBUG_TRACE(...) ((void)0)
#define spin_lock_bh(x) ((void)0)
#define spin_unlock_bh(x) ((void)0)
#define unlikely(x) (x)
typedef uint32_t u32;
struct net { int unused; };
struct dentry { int unused; };
struct nf_conn { int family; };
struct nf_ct_event { struct nf_conn *ct; };
struct notifier_block { int (*notifier_call)(struct notifier_block *, unsigned long, void *); };
struct nf_ct_event_notifier { int (*ct_event)(unsigned int, const struct nf_ct_event *); };
static struct net init_net;
static struct dentry directory;
static struct dentry *ecm_conntrack_notifier_dentry;
static int ecm_conntrack_notifier_stopped, registered, fail_family, fail_register;
static int refs4, refs6, removed, events4, events6;
static struct dentry *debugfs_create_dir(const char *n, struct dentry *p) { return &directory; }
static void debugfs_remove_recursive(struct dentry *d) { removed++; }
static int ecm_debugfs_create_u32(const char *n, int m, struct dentry *d, u32 *v) { return 1; }
static int nf_ct_l3num(struct nf_conn *ct) { return ct->family; }
static int ecm_conntrack_ipv4_event(unsigned int e, struct nf_conn *ct) { events4++; return NOTIFY_DONE; }
static int ecm_conntrack_ipv6_event(unsigned int e, struct nf_conn *ct) { events6++; return NOTIFY_DONE; }
static int nf_ct_netns_get(struct net *n, int family) {
    if (family == fail_family) return -5;
    if (family == AF_INET) refs4++; else refs6++;
    return 0;
}
static void nf_ct_netns_put(struct net *n, int family) {
    if (family == AF_INET) { assert(refs4 == 1); refs4--; }
    else { assert(refs6 == 1); refs6--; }
}
#ifdef CONFIG_NF_CONNTRACK_CHAIN_EVENTS
static int nf_conntrack_register_notifier(struct net *n, struct notifier_block *nb) {
    if (fail_register) return -123;
    assert(!registered); registered++; return 0;
}
static int nf_conntrack_unregister_notifier(struct net *n, struct notifier_block *nb) {
    assert(registered == 1); registered--; return 0;
}
#else
static void nf_conntrack_register_notifier(struct net *n, const struct nf_ct_event_notifier *nb) {
    assert(!registered); registered++;
}
static void nf_conntrack_unregister_notifier(struct net *n) {
    assert(registered == 1); registered--;
}
#endif
'''
    suffix = r'''
static int dispatch(struct nf_conn *ct) {
    struct nf_ct_event item = { .ct = ct };
#ifdef CONFIG_NF_CONNTRACK_CHAIN_EVENTS
    return ecm_conntrack_notifier.notifier_call(&ecm_conntrack_notifier, 1, &item);
#else
    return ecm_conntrack_notifier.ct_event(1, &item);
#endif
}
int main(void) {
    struct nf_conn ipv4 = { AF_INET }, ipv6 = { AF_INET6 };
    assert(ecm_conntrack_notifier_init(&directory) == 0);
    assert(registered == 1 && refs4 == 1 && refs6 == 1);
    assert(dispatch(&ipv4) == NOTIFY_DONE && events4 == 1);
    assert(dispatch(&ipv6) == NOTIFY_DONE && events6 == 1);
    ecm_conntrack_notifier_stop(1);
    assert(dispatch(&ipv4) == NOTIFY_DONE && events4 == 1);
    ecm_conntrack_notifier_exit();
    assert(!registered && !refs4 && !refs6 && removed == 1);
    for (int family = AF_INET; family <= AF_INET6; family += AF_INET6 - AF_INET) {
        removed = 0; fail_family = family;
        assert(ecm_conntrack_notifier_init(&directory) == -5);
        assert(!registered && !refs4 && !refs6 && removed == 1);
    }
#ifdef CONFIG_NF_CONNTRACK_CHAIN_EVENTS
    fail_family = 0; fail_register = 1; removed = 0;
    assert(ecm_conntrack_notifier_init(&directory) == -123);
    assert(!registered && !refs4 && !refs6 && removed == 1);
#endif
    return 0;
}
'''
    unit = tmp / 'test.c'
    unit.write_text(prefix + text + suffix)
    for chain in (False, True):
        binary = tmp / ('chain' if chain else 'single')
        command = ['cc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                   '-Wno-unused-parameter', '-Wno-unused-variable']
        if chain:
            command += ['-DCONFIG_NF_CONNTRACK_CHAIN_EVENTS=1']
        subprocess.run(command + [str(unit), '-o', str(binary)], check=True)
        subprocess.run([str(binary)], check=True)
        print(f'PASS: ECM {binary.name} API types, dispatch and failure cleanup')
