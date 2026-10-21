#!/usr/bin/env python3
"""Attach to the running boot-test VM and run the in-guest verify."""
import os, socket, subprocess, sys, time

W = sys.argv[1]
MON = os.path.join(W, "mon.sock")

def mon(cmds, drain=0.25):
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(MON); s.settimeout(3)
    try: s.recv(4096)
    except Exception: pass
    for c in cmds:
        s.sendall((c + "\n").encode()); time.sleep(0.02)
    time.sleep(drain)
    try:
        while True:
            if not s.recv(4096): break
    except Exception: pass
    s.close()

def shot(tag):
    ppm = os.path.join(W, "shot-%s.ppm" % tag)
    mon(["screendump " + ppm], 0.7)
    return ppm

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
})

def type_text(text):
    cmds = ["sendkey " + KEYMAP[ch] for ch in text]
    mon(cmds, 0.3)

shot("attach")
mon(["sendkey ctrl-alt-t"], 0.5)
time.sleep(4)
shot("terminal")
cmd = ("echo oniontest42 | sudo -S bash -c \"dmsetup table --showkeys > /home/testuser/verify.txt; "
       "systemctl is-active onionhost-config onionhost-images onionhost-nft-load onionhost-nft-gate onionhost-a onionhost-b onionhost-u >> /home/testuser/verify.txt; "
       "podman ps >> /home/testuser/verify.txt; ss -ltn >> /home/testuser/verify.txt; "
       "journalctl -b -u onionhost-a --no-pager -n 25 >> /home/testuser/verify.txt; "
       "ls /var/lib/onionhost >> /home/testuser/verify.txt; sync; poweroff\"")
type_text(cmd)
mon(["sendkey ret"], 0.2)
print("VERIFY_TYPED", flush=True)
time.sleep(45)
shot("after-verify")
print("DONE", flush=True)
