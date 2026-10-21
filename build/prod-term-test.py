#!/usr/bin/env python3
"""Prod live session: open a terminal via monitor mouse, test sudo."""
import socket, sys, time

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

def type_text(text):
    mon(["sendkey " + KEYMAP[ch] for ch in text], 0.3)

def click(x, y):
    mon(["mouse_move %d %d" % (x, y), "mouse_button 1"], 0.15)
    mon(["mouse_button 0"], 0.3)

# terminal icon in the taskbar (2nd icon, ~567,772)
click(567, 772)
time.sleep(3)
mon(["screendump /home/rig/step3-test/shot-prod-term1.ppm"], 0.5)
type_text("sudo -n id; echo SUDOCHECK done; sudo -E calamares > /tmp/cal.log 2>&1 &")
mon(["sendkey ret"], 0.3)
print("typed", flush=True)
time.sleep(6)
mon(["screendump /home/rig/step3-test/shot-prod-term2.ppm"], 0.5)
print("DONE", flush=True)
