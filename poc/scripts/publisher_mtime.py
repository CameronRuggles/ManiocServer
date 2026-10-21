#!/usr/bin/env python3
"""Set a file's mtime the OnionHost publisher way (DESIGN-v3 A8):
mtime = FIXED_EPOCH + (sha256(content) mod 10^8) seconds.
Prints "<epoch> <sha256>" for logging. Content-derived: any edit changes
the hash and therefore the mtime/ETag; no wall-clock edit time leaks.
"""
import hashlib
import os
import sys

FIXED_EPOCH = 1577836800  # 2020-01-01T00:00:00Z; arbitrary fixed base.


def main():
    path = sys.argv[1]
    with open(path, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    epoch = FIXED_EPOCH + (int(digest, 16) % 100_000_000)
    os.utime(path, (epoch, epoch))
    print(f"{epoch} {digest}")


if __name__ == "__main__":
    main()
