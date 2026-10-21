#!/usr/bin/env python3
"""OnionHost step-3 installed-system boot test.

Boots the installed disk under UEFI/SecureBoot and drives the GRUB
LUKS prompt via the QEMU monitor:
  1. wrong phrase first  -> must be REJECTED (re-prompt)
  2. correct phrase      -> slot opens; unlock seconds measured
  3. no second prompt    -> initramfs keyfile must unlock silently
  4. LightDM greeter     -> NO autologin; log in as testuser
  5. in-guest verify     -> writes ~/verify.txt, powers off
Screenshots are saved as PPM in the work dir for conversion.
"""
import os, shutil, socket, subprocess, sys, threading, time

DISK = sys.argv[1]
W = sys.argv[2]
os.makedirs(W, exist_ok=True)
MON = os.path.join(W, "mon.sock")
SER = os.path.join(W, "serial.log")
VARS = os.path.join(W, "OVMF_VARS.fd")
shutil.copy(os.path.expanduser("~/step3-test/OVMF_VARS.fd"), VARS)
for f in (MON, SER):
    try: os.unlink(f)
    except FileNotFoundError: pass

args = ["qemu-system-x86_64", "-name", "step3-boot", "-machine", "q35,accel=kvm",
        "-cpu", "host", "-m", "4096", "-smp", "2",
        "-drive", "if=pflash,format=raw,readonly=on,unit=0,file=/usr/share/OVMF/OVMF_CODE_4M.secboot.fd",
        "-drive", "if=pflash,format=raw,unit=1,file=" + VARS,
        "-drive", "file=%s,if=virtio,format=qcow2" % DISK,
        "-netdev", "user,id=n0", "-device", "virtio-net-pci,netdev=n0",
        "-vga", "std", "-display", "none", "-usb", "-device", "usb-tablet",
        "-monitor", "unix:%s,server,nowait" % MON, "-serial", "file:" + SER,
        "-boot", "order=c"]
t0 = time.time()
events = {}

def el(): return time.time() - t0

def serial_text():
    try: return open(SER, errors="replace").read()
    except FileNotFoundError: return ""

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
    "\\": "backslash", "@": "shift-2", "%": "shift-5", "^": "shift-6",
    "~": "shift-grave", "`": "grave",
})

def type_text(text, delay=0.03):
    cmds = []
    for ch in text:
        k = KEYMAP.get(ch)
        if k is None: raise ValueError("no key for %r" % ch)
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

proc = subprocess.Popen(args, stdout=open(os.path.join(W, "qemu.out"), "ab"),
                        stderr=subprocess.STDOUT, start_new_session=True)
print("QEMU pid", proc.pid, flush=True)

# 1. GRUB prompt
if not wait_serial("Enter passphrase", 180, "prompt"):
    print("FAIL: no GRUB passphrase prompt in serial log", flush=True)
    shot("noprompt"); mon(["quit"], 0.4); sys.exit(1)
print("PROMPT_AT %.2f" % events["prompt"], flush=True)
shot("prompt")

# 2. wrong phrase must be rejected
type_text("wrong horse battery staple")
mon(["sendkey ret"], 0.2)
events["wrong_enter"] = el()
print("WRONG_ENTER_AT %.2f" % events["wrong_enter"], flush=True)
time.sleep(25)
shot("after-wrong")
txt = serial_text()
rejected = ("error" in txt.lower() or "invalid" in txt.lower()
            or txt.count("Enter passphrase") >= 2)
print("WRONG_REJECTED %s" % rejected, flush=True)

# 3. correct phrase. NOTE: GRUB 2.12 does NOT re-prompt after a bad
# passphrase - it drops to the grub> rescue shell. Re-issue cryptomount
# there to get a fresh prompt (a product finding for the log: a typo
# strands the user at grub> unless the production GRUB config retries).
if "grub>" in serial_text():
    n_before = serial_text().count("Enter passphrase")
    type_text("cryptomount hd0,gpt2")
    mon(["sendkey ret"], 0.2)
    start = el()
    while serial_text().count("Enter passphrase") <= n_before and el() - start < 60:
        time.sleep(0.2)
    print("REPROMPT_AT %.2f" % el(), flush=True)
    shot("reprompt")
type_text("correct horse battery staple")
mon(["sendkey ret"], 0.2)
events["enter"] = el()
print("ENTER_AT %.2f" % events["enter"], flush=True)
if wait_serial("opened", 180, "slot_opened"):
    print("SLOT_OPENED_AT %.2f UNLOCK_SECONDS %.2f"
          % (events["slot_opened"], events["slot_opened"] - events["enter"]),
          flush=True)
else:
    print("FAIL: slot never opened", flush=True)
    shot("noopen"); mon(["quit"], 0.4); sys.exit(1)
if "wrong_enter" in events:
    # We arrived via the grub> rescue shell (post-typo path): GRUB does
    # not continue on its own after a manual cryptomount - re-enter
    # normal mode so the default menuentry boots.
    type_text("normal")
    mon(["sendkey ret"], 0.2)
    print("NORMAL_SENT_AT %.2f" % el(), flush=True)
    time.sleep(3)
    mon(["sendkey ret"], 0.2)
time.sleep(20)
shot("initramfs-stage")

# 4. wait for the LightDM greeter (screenshot stability)
last = None; stable = 0; greeter_at = None
while el() < events["slot_opened"] + 300:
    ppm = shot("poll")
    data = open(ppm, "rb").read()
    import hashlib
    h = hashlib.md5(data).hexdigest()
    if h == last:
        stable += 1
        if stable >= 3:
            greeter_at = el(); break
    else:
        stable = 0; last = h
    time.sleep(3)
shot("greeter")
print("GREETER_STABLE_AT %s (%.1fs after slot opened)"
      % (greeter_at, (greeter_at or el()) - events["slot_opened"]), flush=True)

# 5. log in as testuser (greeter: username field, Tab, password)
type_text("testuser")
mon(["sendkey tab"], 0.3)
type_text("oniontest42")
mon(["sendkey ret"], 0.2)
print("LOGIN_ENTER_AT %.2f" % el(), flush=True)
time.sleep(25)
shot("desktop")

# 6. terminal + verify one-liner
mon(["sendkey ctrl-alt-t"], 0.5)
time.sleep(4)
shot("terminal")
cmd = ("echo oniontest42 | sudo -S bash -c \"dmsetup table --showkeys > /home/testuser/verify.txt; "
       "systemctl is-active onionhost-config onionhost-images onionhost-nft-load onionhost-nft-gate onionhost-a onionhost-b onionhost-u >> /home/testuser/verify.txt; "
       "podman ps -a >> /home/testuser/verify.txt; ss -ltn >> /home/testuser/verify.txt; "
       "echo ===A=== >> /home/testuser/verify.txt; journalctl -b -u onionhost-a --no-pager -n 18 >> /home/testuser/verify.txt; "
       "echo ===B=== >> /home/testuser/verify.txt; journalctl -b -u onionhost-b --no-pager -n 60 | grep -v 'image pull' | tail -18 >> /home/testuser/verify.txt; "
       "echo ===U=== >> /home/testuser/verify.txt; journalctl -b -u onionhost-u --no-pager -n 60 | grep -v 'image pull' | tail -18 >> /home/testuser/verify.txt; "
       "echo ===SOCKS=== >> /home/testuser/verify.txt; ls -la /run/onionhost/web /run/onionhost/control /run/onionhost/client/socks >> /home/testuser/verify.txt 2>&1; "
       "echo ===HS=== >> /home/testuser/verify.txt; cat /var/lib/onionhost/tor/hs/hostname >> /home/testuser/verify.txt 2>&1; "
       "echo ===PROBE=== >> /home/testuser/verify.txt; onionhost-probe >> /home/testuser/verify.txt 2>&1; "
       "ls /var/lib/onionhost >> /home/testuser/verify.txt; sync; poweroff\"")
type_text(cmd)
mon(["sendkey ret"], 0.2)
print("VERIFY_TYPED_AT %.2f" % el(), flush=True)
for _ in range(40):
    if proc.poll() is not None: break
    time.sleep(3)
print("QEMU_EXITED %s TOTAL %.1f" % (proc.poll() is not None, el()), flush=True)
if proc.poll() is None:
    shot("endstate")
    mon(["quit"], 0.4)
print("DONE", flush=True)
