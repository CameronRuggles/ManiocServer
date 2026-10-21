#!/usr/bin/env python3
"""Debug: log the exact argv conmon/podman passes to the runtime."""
import os, socket, sys, time

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

time.sleep(15)
mon(["sendkey ctrl-alt-t"], 0.5)
time.sleep(4)
cmd = ("echo oniontest42 | sudo -S bash -c 'systemctl stop onionhost-a onionhost-b onionhost-u; "
       "printf \"%s\\n\" \"#!/bin/sh\" \"echo ARGS: \\$@ >> /tmp/argv.log\" \"exec /usr/local/bin/runsc-wrap \\$@\" > /tmp/wrapdbg; "
       "chmod +x /tmp/wrapdbg; "
       "timeout 12 podman run --rm --runtime=/tmp/wrapdbg --network=host --userns=auto localhost/onionhost-tor:latest > /home/testuser/runout.txt 2>&1; "
       "cp /tmp/argv.log /home/testuser/argv.txt; "
       "grep -o \"network[^]]*\" /run/containers/storage/overlay-containers/*/userdata/config.json > /home/testuser/specnet.txt 2>/dev/null; "
       "chown testuser:testuser /home/testuser/runout.txt /home/testuser/argv.txt /home/testuser/specnet.txt 2>/dev/null; sync; poweroff'")
type_text(cmd)
mon(["sendkey ret"], 0.2)
print("DBG_TYPED", flush=True)
time.sleep(50)
print("DONE", flush=True)
