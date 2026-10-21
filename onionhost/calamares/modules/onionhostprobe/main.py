# SPDX-License-Identifier: GPL-3.0-or-later
"""OnionHost PROBE jobmodule (diagnostics only - never in a release ISO).

Runs inside the Calamares exec phase and records which GlobalStorage
keys exist and how the partition data is structured, so the real
onionhostbootkey module can be written against facts instead of
assumptions. SECRET DISCIPLINE: it never writes secret VALUES to disk -
for passphrase-like fields it records only presence, type and length.
Output: /tmp/gsprobe.txt in the live session.
"""
import libcalamares


def _describe(value, depth=0):
    """Structural description of a GS value with secrets redacted."""
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            lk = str(k).lower()
            if "pass" in lk or "secret" in lk or "key" == lk:
                out[k] = "<redacted: type=%s len=%s>" % (
                    type(v).__name__,
                    len(v) if hasattr(v, "__len__") else "?")
            elif depth < 2:
                out[k] = _describe(v, depth + 1)
            else:
                out[k] = "<%s>" % type(v).__name__
        return out
    if isinstance(value, (list, tuple)):
        return [_describe(v, depth + 1) for v in value]
    if isinstance(value, str) and len(value) > 80:
        return value[:80] + "...<str len=%d>" % len(value)
    return value


def run():
    gs = libcalamares.globalstorage
    lines = []
    try:
        keys = list(gs.keys())
    except Exception as e:
        keys = []
        lines.append("gs.keys() failed: %r" % e)
    lines.append("GS KEYS: %s" % ", ".join(sorted(str(k) for k in keys)))
    for probe_key in ("luksPassphrase", "encryptPassphrase",
                      "rootMountPoint", "partitions", "mountPoint",
                      "firmwareType", "bootLoader"):
        try:
            present = gs.contains(probe_key)
        except Exception:
            present = "?"
        lines.append("KEY %s present=%s" % (probe_key, present))
        if present is True:
            try:
                lines.append("  VALUE: %r" % _describe(gs.value(probe_key)))
            except Exception as e:
                lines.append("  describe failed: %r" % e)
    with open("/tmp/gsprobe.txt", "w") as f:
        f.write("\n".join(lines) + "\n")
    return None
