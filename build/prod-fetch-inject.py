#!/usr/bin/env python3
"""In the prod live session: raise the terminal (Alt+Tab), fetch the
mouse injector from the rig via the QEMU gateway, run a proof click
on the Calamares error dialog's Close button."""
import socket, time

MON = "/home/rig/step3-test/mon.sock"

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
    mon(["sendkey " + KEYMAP[c] for c in t], 0.3)

mon(["sendkey alt-tab"], 0.5)
time.sleep(2)
mon(["screendump /home/rig/step3-test/shot-kbd.ppm"], 0.5)
print("raised", flush=True)
