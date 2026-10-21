#!/usr/bin/env python3
"""Slice-2 console helper: type text / take screenshots via a QEMU
monitor socket. Env: S2MON (monitor sock path), S2DIR (work dir)."""
import os
import socket
import sys
import time

MON = os.environ.get("S2MON", "/home/rig/slice2/mon.sock")
DIR = os.environ.get("S2DIR", "/home/rig/slice2")

KEYMAP = {}
for ch in "abcdefghijklmnopqrstuvwxyz0123456789":
    KEYMAP[ch] = ch
for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
    KEYMAP[ch] = "shift-" + ch.lower()
KEYMAP.update({
    " ": "spc", "-": "minus", "_": "shift-minus", "=": "equal",
    ".": "dot", ",": "comma", "/": "slash", ";": "semicolon",
    ":": "shift-semicolon", "'": "apostrophe", '"': "shift-apostrophe",
    "|": "shift-backslash", ">": "shift-dot", "<": "shift-comma",
    "(": "shift-9", ")": "shift-0", "$": "shift-4", "&": "shift-7",
    "*": "shift-8", "+": "shift-equal", "#": "shift-3", "!": "shift-1",
    "?": "shift-slash", "[": "bracket_left", "]": "bracket_right",
    "\\": "backslash", "@": "shift-2", "%": "shift-5", "^": "shift-6",
    "~": "shift-grave", "`": "grave", "\n": "ret", "\t": "tab",
})


def mon(cmds, drain=0.25):
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(MON)
    s.settimeout(3)
    try:
        s.recv(4096)
    except Exception:
        pass
    for c in cmds:
        s.sendall((c + "\n").encode())
        time.sleep(0.02)
    time.sleep(drain)
    try:
        while True:
            if not s.recv(4096):
                break
    except Exception:
        pass
    s.close()


def main():
    op = sys.argv[1]
    if op == "type":
        text = sys.argv[2]
        mon(["sendkey " + KEYMAP[ch] for ch in text], 0.4)
    elif op == "key":
        mon(["sendkey " + sys.argv[2]], 0.4)
    elif op == "click":
        mon(["mouse_move %s %s" % (sys.argv[2], sys.argv[3])], 0.3)
        mon(["mouse_button 1"], 0.2)
        mon(["mouse_button 0"], 0.3)
    elif op == "shot":
        ppm = os.path.join(DIR, sys.argv[2] + ".ppm")
        mon(["screendump " + ppm], 0.9)
        print(ppm)
    elif op == "cmd":
        mon(["sendkey " + KEYMAP[ch] for ch in sys.argv[2] + "\n"], 0.4)
    else:
        print("ops: type|key|click|shot|cmd")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
