#!/usr/bin/env python3
"""Keyboard-drive helper for the prod Calamares (monitor sendkey).

Usage: prod-kbd-drive.py <step>
  next      : Alt+N (advance one page), screenshot
  shot      : screenshot only
  erase     : on Partitions: try focus dance for Erase radio (see log)
"""
import socket, sys, time

MON = "/home/rig/step3-test/mon.sock"
W = "/home/rig/step3-test"

def mon(cmds, drain=0.3):
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(MON); s.settimeout(3)
    try: s.recv(4096)
    except Exception: pass
    for c in cmds:
        s.sendall((c + "\n").encode()); time.sleep(0.03)
    time.sleep(drain)
    try:
        while True:
            if not s.recv(4096): break
    except Exception: pass
    s.close()

def shot(name):
    mon(["screendump %s/%s.ppm" % (W, name)], 0.5)

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
    "\\": "backslash", "~": "shift-grave", "%": "shift-5", "^": "shift-6",
    "@": "shift-2", "{": "shift-bracket_left", "}": "shift-bracket_right",
    "`": "grave",
})

def typ(t):
    mon(["sendkey " + KEYMAP[c] for c in t], 0.25)

step = sys.argv[1]
if step == "next":
    mon(["sendkey alt-n"], 0.5)
    time.sleep(3)
    shot("shot-kbd")
elif step == "shot":
    shot("shot-kbd")
elif step == "tab":
    mon(["sendkey tab"], 0.4)
    time.sleep(1)
    shot("shot-kbd")
elif step == "space":
    mon(["sendkey spc"], 0.4)
    time.sleep(1)
    shot("shot-kbd")
elif step == "down":
    mon(["sendkey down"], 0.4)
    time.sleep(1)
    shot("shot-kbd")
elif step == "type":
    typ(sys.argv[2])
    time.sleep(1)
    shot("shot-kbd")
print("STEP-DONE", step, flush=True)
