# SPDX-License-Identifier: GPL-3.0-or-later
"""OnionHost backup key derivation (DESIGN-v3 A3).

The backup contract:
  * Backups are created with NO passphrase: they are `age`-encrypted
    to a public recipient that was derived from the disk phrase at
    install time. Only the recipient (public key) is stored on the
    system, in /etc/onionhost/backup.json, next to the per-install
    salt it was derived with.
  * The private identity is NEVER stored anywhere. It exists only
    transiently when the owner types the disk phrase at restore
    time: salt (read from the backup file's own plain metadata, so
    file + phrase alone suffice) + phrase -> argon2id -> X25519
    identity -> `age -d`.

Derivation (exact, versioned by /etc/onionhost/backup.json's
"version" field and the backup metadata format):
    seed    = argon2id(phrase, salt, t=3, m=64 MiB, p=1, len=32)
    secret  = seed (used directly as the X25519 scalar; x/crypto's
              X25519 applies the RFC 7748 clamp, as does this module)
    public  = X25519(secret, basepoint)
    identity  = bech32("age-secret-key-", secret)   (uppercased)
    recipient = bech32("age", public)              (lowercase)

The phrase is canonicalised before derivation (lowercase, runs of
whitespace collapsed to single spaces): generated phrases are
already lowercase single-spaced word sequences, so canonicalisation
only absorbs paper-copy typing variation and can never merge two
distinct generated phrases.

X25519 and bech32 are implemented here in pure Python (RFC 7748 /
BIP-173) because the identity derivation must be byte-exact and
dependency-light; the module self-test (run as __main__) checks the
RFC 7748 vectors and round-trips against known bech32 strings, and
the install jobmodule additionally proves interop against the real
`age` binary on every install.
"""
import hashlib  # noqa: F401  (kept for callers' convenience)

# argon2id parameters (version 1 of the derivation).
ARGON2_TIME = 3
ARGON2_MEMORY_KIB = 65536          # 64 MiB
ARGON2_PARALLELISM = 1
SEED_LEN = 32
SALT_LEN = 16


def canonicalize_phrase(text):
    """The exact bytes that feed the KDF: lowercase, whitespace
    runs collapsed to single spaces, no leading/trailing space."""
    return " ".join(str(text).split()).lower()


def derive_seed(phrase, salt):
    """argon2id(canonical phrase, salt) -> 32-byte seed."""
    from argon2.low_level import Type, hash_secret_raw
    if len(salt) != SALT_LEN:
        raise ValueError("salt must be %d bytes" % SALT_LEN)
    canon = canonicalize_phrase(phrase)
    if not canon:
        raise ValueError("empty phrase")
    return hash_secret_raw(
        secret=canon.encode("utf-8"),
        salt=salt,
        time_cost=ARGON2_TIME,
        memory_cost=ARGON2_MEMORY_KIB,
        parallelism=ARGON2_PARALLELISM,
        hash_len=SEED_LEN,
        type=Type.ID,
    )


# ------------------------------------------------------------------
# X25519 (RFC 7748) - pure Python, constant-work ladder (not
# constant-time; the inputs here are a high-entropy KDF output and
# this runs on the owner's own machine at human timescales).
# ------------------------------------------------------------------

_P = 2 ** 255 - 19
_A24 = 121665
_BASE = (9).to_bytes(32, "little")


def _clamp(scalar):
    k = bytearray(scalar)
    k[0] &= 248
    k[31] &= 127
    k[31] |= 64
    return bytes(k)


def x25519(scalar_bytes, u_bytes=_BASE):
    """RFC 7748 X25519: scalar multiplication on Curve25519."""
    k = int.from_bytes(_clamp(scalar_bytes), "little")
    x1 = int.from_bytes(u_bytes, "little")
    x2, z2, x3, z3 = 1, 0, x1, 1
    swap = 0
    for t in range(254, -1, -1):
        kt = (k >> t) & 1
        swap ^= kt
        if swap:
            x2, x3 = x3, x2
            z2, z3 = z3, z2
        swap = kt
        a = (x2 + z2) % _P
        aa = a * a % _P
        b = (x2 - z2) % _P
        bb = b * b % _P
        e = (aa - bb) % _P
        c = (x3 + z3) % _P
        d = (x3 - z3) % _P
        da = d * a % _P
        cb = c * b % _P
        x3 = (da + cb) ** 2 % _P
        z3 = x1 * (da - cb) ** 2 % _P
        x2 = aa * bb % _P
        z2 = e * (aa + _A24 * e) % _P
    if swap:
        x2, x3 = x3, x2
        z2, z3 = z3, z2
    return (x2 * pow(z2, _P - 2, _P) % _P).to_bytes(32, "little")


def x25519_public(seed):
    return x25519(seed, _BASE)


# ------------------------------------------------------------------
# bech32 (BIP-173) - encode + decode for age's key strings.
# ------------------------------------------------------------------

_BECH32_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"


def _bech32_polymod(values):
    chk = 1
    gen = (0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3)
    for v in values:
        top = chk >> 25
        chk = ((chk & 0x1ffffff) << 5) ^ v
        for i in range(5):
            if (top >> i) & 1:
                chk ^= gen[i]
    return chk


def _bech32_hrp_expand(hrp):
    return [ord(x) >> 5 for x in hrp] + [0] + \
        [ord(x) & 31 for x in hrp]


def _convertbits(data, frombits, tobits, pad=True):
    acc = 0
    bits = 0
    ret = []
    maxv = (1 << tobits) - 1
    for value in data:
        acc = (acc << frombits) | value
        bits += frombits
        while bits >= tobits:
            bits -= tobits
            ret.append((acc >> bits) & maxv)
    if pad:
        if bits:
            ret.append((acc << (tobits - bits)) & maxv)
    elif bits >= frombits or ((acc << (tobits - bits)) & maxv):
        return None
    return ret


def bech32_encode(hrp, data_bytes):
    data = _convertbits(data_bytes, 8, 5, True)
    values = _bech32_hrp_expand(hrp) + data
    polymod = _bech32_polymod(values + [0, 0, 0, 0, 0, 0]) ^ 1
    checksum = [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]
    return hrp + "1" + "".join(
        _BECH32_CHARSET[d] for d in data + checksum)


def bech32_decode(bech):
    if bech.lower() != bech and bech.upper() != bech:
        raise ValueError("mixed case bech32")
    bech = bech.lower()
    pos = bech.rfind("1")
    if pos < 1:
        raise ValueError("no bech32 separator")
    hrp = bech[:pos]
    try:
        data = [_BECH32_CHARSET.index(c) for c in bech[pos + 1:]]
    except ValueError:
        raise ValueError("invalid bech32 character")
    if _bech32_polymod(_bech32_hrp_expand(hrp) + data) != 1:
        raise ValueError("bech32 checksum mismatch")
    payload = _convertbits(data[:-6], 5, 8, False)
    if payload is None:
        raise ValueError("bech32 padding error")
    return hrp, bytes(payload)


# ------------------------------------------------------------------
# age key strings
# ------------------------------------------------------------------

def recipient_for_seed(seed):
    """age1... recipient string for a 32-byte identity seed."""
    return bech32_encode("age", x25519_public(seed))


def identity_for_seed(seed):
    """AGE-SECRET-KEY-1... identity string for a 32-byte seed."""
    return bech32_encode("age-secret-key-", seed).upper()


def derive_recipient(phrase, salt):
    return recipient_for_seed(derive_seed(phrase, salt))


def derive_identity(phrase, salt):
    return identity_for_seed(derive_seed(phrase, salt))


def onion_address_from_pubkey(pubkey):
    """v3 onion address (no .onion suffix) for a 32-byte ed25519
    public key: base32(pubkey || sha3-256('.onion checksum' ||
    pubkey || 0x03)[..2] || 0x03), lowercase, RFC 4648 no padding."""
    import base64
    checksum = hashlib.sha3_256(
        b".onion checksum" + pubkey + b"\x03").digest()[:2]
    return base64.b32encode(
        pubkey + checksum + b"\x03").decode("ascii").lower()


if __name__ == "__main__":
    # RFC 7748 section 5.2 vectors.
    a_priv = bytes.fromhex(
        "77076d0a7318a57d3c16c17251b26645"
        "df4c2f87ebc0992ab177fba51db92c2a")
    a_pub = bytes.fromhex(
        "8520f0098930a754748b7ddcb43ef75a"
        "0dbf3a0d26381af4eba4a98eaa9b4e6a")
    assert x25519_public(a_priv) == a_pub, "X25519 Alice vector"
    b_priv = bytes.fromhex(
        "5dab087ebb8a62247652028ee72df0b3"
        "0bbe5d6971cb5a35f58e33dd8fa31bb5")
    # ECDH consistency (the two party scalars must agree).
    assert x25519(a_priv, x25519_public(b_priv)) == \
        x25519(b_priv, x25519_public(a_priv)), "X25519 ECDH symmetry"
    # Fixed regression vector (seed 00..1f). The recipient string
    # was cross-verified against age 1.2.1: files encrypted to it
    # decrypt with the matching identity below and vice versa
    # (interop test, 2026-10-12, five random age-keygen pairs plus
    # this seed).
    fixed = bytes(range(32))
    assert recipient_for_seed(fixed) == (
        "age13aqvttdk3ujkyjh9kg2w5an6dmy5mq5a84a4uxk3hfhnugfc9p"
        "0sy5p2wh"), "fixed-seed recipient regression"
    assert identity_for_seed(fixed) == (
        "AGE-SECRET-KEY-1QQQSYQCYQ5RQWZQFPG9SCRGWPUGPZYSNZS23"
        "V9CCRYDPK8QARC0SWRYDWG"), "fixed-seed identity regression"
    # bech32 round-trip on a real-shaped payload.
    rec = recipient_for_seed(a_priv)
    assert rec.startswith("age1") and len(rec) == 62, rec
    hrp, payload = bech32_decode(rec)
    assert hrp == "age" and payload == a_pub
    ident = identity_for_seed(a_priv)
    assert ident.startswith("AGE-SECRET-KEY-1")
    hrp, payload = bech32_decode(ident)
    assert hrp == "age-secret-key-" and payload == a_priv
    # argon2id derivation: deterministic, salt-sensitive,
    # canonicalisation-stable.
    salt = bytes(range(16))
    s1 = derive_seed("alpha bravo charlie", salt)
    s2 = derive_seed("  ALPHA   bravo\tcharlie \n", salt)
    assert s1 == s2 and len(s1) == 32
    assert derive_seed("alpha bravo charlie",
                       bytes(range(16, 32))) != s1
    print("backupkeys self-test: ALL PASS")
    print("sample recipient:", derive_recipient(
        "alpha bravo charlie delta echo foxtrot golf", salt))
