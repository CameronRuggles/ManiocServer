#!/usr/bin/env python3
"""OnionHost step-3 slice-2 installed-system boot driver.

Generalised from boottest3.py. Behaviour is env-driven:

  DISK, W            disk image + work dir (required)
  MODE               loop | unlock | hold | spareboot
  PHRASE_WRONG       typed first in loop mode
  PHRASE             the phrase to unlock with (main by default)
  LOGIN_USER/PHRASE  greeter login after unlock (optional; skipped
                     in hold mode)
  CMD                one-liner typed into a terminal after login
                     (should write ~/verify.txt and poweroff)
  HOLD_SECS          in hold mode: seconds to stay up after unlock
                     before quitting (parent curls the onion meanwhile)
  KILL9_AFTER        if set (seconds after start), hard-kill QEMU
                     instead of a clean flow (power-pull tests)

Serial log + PPM screenshots land in W.
"""
import hashlib
import os
import shutil
import socket
import subprocess
import sys
import time

DISK = os.environ["DISK"]
W = os.environ["W"]
MODE = os.environ.get("MODE", "loop")
os.makedirs(W, exist_ok=True)
MON = os.path.join(W, "mon.sock")
SER = os.path.join(W, "serial.log")
VARS = os.path.join(W, "OVMF_VARS.fd")
if not os.path.exists(VARS):
    shutil.copy(os.path.expanduser("~/step3-test/OVMF_VARS.fd"), VARS)
for f in (MON, SER):
    try:
        os.unlink(f)
    except FileNotFoundError:
        pass

args = ["qemu-system-x86_64", "-name", "slice2-boot", "-machine",
        "q35,accel=kvm", "-cpu", "host", "-m", "4096", "-smp", "2",
        "-drive", "if=pflash,format=raw,readonly=on,unit=0,"
        "file=/usr/share/OVMF/OVMF_CODE_4M.secboot.fd",
        "-drive", "if=pflash,format=raw,unit=1,file=" + VARS,
        "-drive", "file=%s,if=virtio,format=qcow2" % DISK,
        "-netdev", "user,id=n0", "-device", "virtio-net-pci,netdev=n0",
        "-vga", "std", "-display", "none", "-usb", "-device", "usb-tablet",
        "-monitor", "unix:%s,server,nowait" % MON,
        "-serial", "file:" + SER, "-boot", "order=c"]
t0 = time.time()
events = {}


def el():
    return time.time() - t0


def serial_text():
    try:
        return open(SER, errors="replace").read()
    except FileNotFoundError:
        return ""


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
    "\\": "backslash", "@": "shift-2", "%": "shift-5", "^": "shift-6",
    "~": "shift-grave", "`": "grave",
})


def type_text(text, delay=0.03):
    cmds = []
    for ch in text:
        k = KEYMAP.get(ch)
        if k is None:
            raise ValueError("no key for %r" % ch)
        cmds.append("sendkey " + k)
    mon(cmds, 0.3)
    time.sleep(delay * len(text) * 0.2)


def wait_serial(needle, timeout, label):
    start = el()
    while el() - start < timeout:
        if needle in serial_text():
            events[label] = el()
            return True
        time.sleep(0.2)
    return False


proc = subprocess.Popen(args, stdout=open(os.path.join(W, "qemu.out"),
                                          "ab"),
                        stderr=subprocess.STDOUT, start_new_session=True)
print("QEMU pid", proc.pid, flush=True)

kill9_after = os.environ.get("KILL9_AFTER")
if kill9_after:
    time.sleep(float(kill9_after))
    proc.kill()
    print("KILLED9_AT %.1f" % el(), flush=True)
    sys.exit(0)

if not wait_serial("Enter passphrase", 180, "prompt"):
    print("FAIL: no GRUB passphrase prompt", flush=True)
    shot("noprompt")
    mon(["quit"], 0.4)
    sys.exit(1)
print("PROMPT_AT %.2f" % events["prompt"], flush=True)
shot("prompt")

if MODE == "loop":
    type_text(os.environ["PHRASE_WRONG"])
    mon(["sendkey ret"], 0.2)
    events["wrong_enter"] = el()
    print("WRONG_ENTER_AT %.2f" % events["wrong_enter"], flush=True)
    # wait for the retry loop to re-prompt (slice-2 behaviour)
    start = el()
    reprompt = False
    while el() - start < 120:
        if serial_text().count("Enter passphrase") >= 2:
            reprompt = True
            events["reprompt"] = el()
            break
        time.sleep(0.5)
    print("REPROMPT %s AT %s" % (reprompt, events.get("reprompt")),
          flush=True)
    shot("after-wrong")
    in_rescue = "\ngrub>" in serial_text() or \
        serial_text().rstrip().endswith("grub>")
    print("AT_RESCUE_SHELL %s" % in_rescue, flush=True)

phrase = os.environ["PHRASE"]
type_text(phrase)
mon(["sendkey ret"], 0.2)
events["enter"] = el()
print("ENTER_AT %.2f" % events["enter"], flush=True)
if wait_serial("opened", 240, "slot_opened"):
    print("SLOT_OPENED_AT %.2f UNLOCK_SECONDS %.2f"
          % (events["slot_opened"],
             events["slot_opened"] - events["enter"]), flush=True)
else:
    print("FAIL: slot never opened", flush=True)
    shot("noopen")
    mon(["quit"], 0.4)
    sys.exit(1)

if MODE == "hold":
    hold = float(os.environ.get("HOLD_SECS", "300"))
    print("HOLDING %.0fs" % hold, flush=True)
    time.sleep(hold)
    shot("hold-end")
    mon(["quit"], 0.4)
    print("DONE", flush=True)
    sys.exit(0)

# wait for a stable graphical screen (greeter or autologin session)
last = None
stable = 0
stable_at = None
while el() < events["slot_opened"] + 360:
    ppm = shot("poll")
    data = open(ppm, "rb").read()
    h = hashlib.md5(data).hexdigest()
    if h == last:
        stable += 1
        if stable >= 3:
            stable_at = el()
            break
    else:
        stable = 0
        last = h
    time.sleep(3)
shot("stable-screen")
print("SCREEN_STABLE_AT %s (%.1fs after slot opened)"
      % (stable_at, (stable_at or el()) - events["slot_opened"]),
      flush=True)

user = os.environ.get("LOGIN_USER")
if user:
    type_text(user)
    mon(["sendkey tab"], 0.3)
    type_text(os.environ["LOGIN_PHRASE"])
    mon(["sendkey ret"], 0.2)
    print("LOGIN_ENTER_AT %.2f" % el(), flush=True)
    time.sleep(25)
    shot("after-login")

cmd = os.environ.get("CMD")
if cmd:
    mon(["sendkey ctrl-alt-t"], 0.5)
    time.sleep(4)
    shot("terminal")
    type_text(cmd)
    mon(["sendkey ret"], 0.2)
    print("CMD_TYPED_AT %.2f" % el(), flush=True)
    for _ in range(60):
        if proc.poll() is not None:
            break
        time.sleep(3)
    print("QEMU_EXITED %s" % (proc.poll() is not None), flush=True)
    if proc.poll() is None:
        shot("endstate")
        mon(["quit"], 0.4)
print("DONE", flush=True)
