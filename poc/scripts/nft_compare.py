#!/usr/bin/env python3
"""Canonicalise two `nft -j list ...` JSON documents and compare them.

Strips kernel-assigned handles/indexes and the metainfo object, preserves
rule order inside chains (order is semantic there), and sorts elements of
sets (order is not semantic there). Prints exactly SAME or DIFFERENT.
Exit: 0 same, 1 different, 2 input error.
"""
import json
import sys

VOLATILE_KEYS = {"handle", "index"}


def normalize(obj, parent_key=None):
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in VOLATILE_KEYS:
                continue
            out[k] = normalize(v, k)
        return out
    if isinstance(obj, list):
        vals = [normalize(v, parent_key) for v in obj]
        # Drop the metainfo object from the top-level nftables list.
        vals = [v for v in vals if not (isinstance(v, dict) and set(v) == {"metainfo"})]
        if parent_key in {"set", "elem", "state"} or (
            parent_key == "right" and vals
            and all(isinstance(x, (str, int)) for x in vals)
        ):
            # Set elements / flag lists: order is not semantic.
            vals.sort(key=lambda x: json.dumps(x, sort_keys=True, separators=(",", ":")))
        return vals
    return obj


def main():
    if len(sys.argv) != 3:
        print("usage: nft_compare.py REF.json LIVE.json", file=sys.stderr)
        return 2
    try:
        with open(sys.argv[1]) as f:
            ref = normalize(json.load(f))
        with open(sys.argv[2]) as f:
            live = normalize(json.load(f))
    except Exception as e:
        print(f"input error: {e}", file=sys.stderr)
        return 2
    if ref == live:
        print("SAME")
        return 0
    print("DIFFERENT")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
