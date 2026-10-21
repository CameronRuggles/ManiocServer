#!/usr/bin/env python3
"""Slice-5B battery driver (runs ON the rig).

Per-guest QEMU lifecycle + monitor interaction, following the
patterns proven in slices 2/4/5A (boottest3.py / qemu-drive.py):
monitor-socket sendkey batching, screendump -> PNG conversion,
serial log file, OVMF Secure Boot pflash, 9p share for
bootstrapping throwaway guests.

Usage:
  s5b.py launch-install <guest> <ssh-port>   # boot the test ISO
  s5b.py launch-disk    <guest> <ssh-port>   # boot installed disk
  s5b.py shot           <guest> <name>
  s5b.py type           <guest> <text>
  s5b.py key            <guest> <sendkey-combo>
  s5b.py mon            <guest> <monitor command...>
  s5b.py status         <guest>
  s5b.py stop           <guest>
Guests live in ~/slice5b/<guest>/ (qcow2, VARS, mon.sock,
serial.log, shots/). The shared bootstrap dir is ~/slice5b/share.
"""
import os
import socket
import struct
import subprocess
import sys
import time
import zlib

BASE = os.path.expanduser("~/slice5b")
ISO = os.path.expanduser("~/iso-build-test/onionhost-test-amd64.iso")
SHARE = os.path.join(BASE, "share")
OVMF_CODE = "/usr/share/OVMF/OVMF_CODE_4M.secboot.fd"
VARS_TEMPLATE = os.path.expanduser("~/step3-test/OVMF_VARS.fd")
if not os.path.exists(VARS_TEMPLATE):
    VARS_TEMPLATE = "/usr/share/OVMF/OVMF_VARS_4M.fd"


def gdir(g):
    return os.path.join(BASE, g)


def mon_path(g):
    return os.path.join(gdir(g), "mon.sock")


def mon(g, cmds, drain=0.3):
    if isinstance(cmds, str):
        cmds = [cmds]
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(mon_path(g))
    s.settimeout(5)
    try:
        s.recv(4096)
    except Exception:
        pass
    for c in cmds:
        s.sendall((c + "\n").encode())
        time.sleep(0.02)
    time.sleep(drain)
    out = b""
    try:
        while True:
            d = s.recv(4096)
            if not d:
                break
            out += d
    except Exception:
        pass
    s.close()
    return out.decode(errors="replace")


def running(g):
    return subprocess.run(
        ["pgrep", "-f", "qemu-system.*-name s5b-%s" % g],
        capture_output=True).returncode == 0


def launch(g, port, install):
    d = gdir(g)
    os.makedirs(os.path.join(d, "shots"), exist_ok=True)
    os.makedirs(SHARE, exist_ok=True)
    disk = os.path.join(d, "disk.qcow2")
    vars_fd = os.path.join(d, "VARS.fd")
    if not os.path.exists(vars_fd):
        subprocess.run(["cp", VARS_TEMPLATE, vars_fd], check=True)
    if not os.path.exists(disk):
        subprocess.run(["qemu-img", "create", "-f", "qcow2", disk,
                        "24G"], check=True)
    for f in (mon_path(g), os.path.join(d, "serial.log")):
        try:
            os.unlink(f)
        except FileNotFoundError:
            pass
    args = ["qemu-system-x86_64", "-name", "s5b-%s" % g,
            "-machine", "q35,accel=kvm", "-cpu", "host",
            "-m", "3072", "-smp", "2",
            "-drive", "if=pflash,format=raw,readonly=on,unit=0,"
                      "file=" + OVMF_CODE,
            "-drive", "if=pflash,format=raw,unit=1,file=" + vars_fd,
            "-drive", "file=%s,if=virtio,format=qcow2" % disk,
            "-netdev", "user,id=n0,hostfwd=tcp:127.0.0.1:%d-:22"
                       % port,
            "-device", "virtio-net-pci,netdev=n0",
            "-virtfs", "local,path=%s,mount_tag=hostshare,"
                       "security_model=none" % SHARE,
            "-vga", "std", "-display", "none",
            "-usb", "-device", "usb-tablet",
            "-monitor", "unix:%s,server,nowait" % mon_path(g),
            "-serial", "file:" + os.path.join(d, "serial.log")]
    if install:
        args += ["-drive", "file=%s,media=cdrom,readonly=on,if=ide"
                           % ISO,
                 "-boot", "order=d,menu=on"]
    else:
        args += ["-boot", "order=c"]
    subprocess.Popen(args, stdout=open(os.path.join(d, "qemu.out"),
                                       "ab"),
                     stderr=subprocess.STDOUT, start_new_session=True)
    for _ in range(60):
        if os.path.exists(mon_path(g)):
            break
        time.sleep(0.25)
    print("launched s5b-%s (install=%s, ssh port %d), monitor: %s"
          % (g, install, port, os.path.exists(mon_path(g))))


def shot(g, name):
    d = gdir(g)
    ppm = os.path.join(d, "shot.ppm")
    png = os.path.join(d, "shots", name + ".png")
    mon(g, "screendump " + ppm, 1.0)
    with open(ppm, "rb") as f:
        f.readline()
        dims = f.readline()
        while dims.startswith(b"#"):
            dims = f.readline()
        f.readline()
        data = f.read()
    w, h = map(int, dims.split())

    def chunk(t, dd):
        c = struct.pack(">I", len(dd)) + t + dd
        return c + struct.pack(">I", zlib.crc32(t + dd) & 0xffffffff)
    raw = b"".join(b"\x00" + data[i * w * 3:(i + 1) * w * 3]
                   for i in range(h))
    pngdata = (b"\x89PNG\r\n\x1a\n"
               + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2,
                                             0, 0, 0))
               + chunk(b"IDAT", zlib.compress(raw))
               + chunk(b"IEND", b""))
    open(png, "wb").write(pngdata)
    print("shot:", png, "%dx%d" % (w, h))


KEYMAP = {}
for _ch in "abcdefghijklmnopqrstuvwxyz0123456789":
    KEYMAP[_ch] = _ch
for _ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
    KEYMAP[_ch] = "shift-" + _ch.lower()
KEYMAP.update({
    " ": "spc", "\n": "ret", "\t": "tab", "-": "minus",
    "_": "shift-minus", "=": "equal", ".": "dot", ",": "comma",
    "/": "slash", ";": "semicolon", ":": "shift-semicolon",
    "'": "apostrophe", '"': "shift-apostrophe",
    "|": "shift-backslash", ">": "shift-dot", "<": "shift-comma",
    "(": "shift-9", ")": "shift-0", "$": "shift-4", "&": "shift-7",
    "*": "shift-8", "+": "shift-equal", "#": "shift-3",
    "!": "shift-1", "?": "shift-slash", "[": "bracket_left",
    "]": "bracket_right", "\\": "backslash", "@": "shift-2",
    "%": "shift-5", "^": "shift-6", "~": "shift-grave",
    "`": "grave",
})


def type_text(g, text):
    cmds = []
    for ch in text:
        k = KEYMAP.get(ch)
        if k is None:
            raise ValueError("no key for %r" % ch)
        cmds.append("sendkey " + k)
    mon(g, cmds, 0.3)
    print("typed %d chars" % len(text))


def main():
    cmd = sys.argv[1]
    g = sys.argv[2]
    if cmd == "launch-install":
        launch(g, int(sys.argv[3]), True)
    elif cmd == "launch-disk":
        launch(g, int(sys.argv[3]), False)
    elif cmd == "shot":
        shot(g, sys.argv[3])
    elif cmd == "type":
        type_text(g, sys.argv[3])
    elif cmd == "key":
        print(mon(g, "sendkey " + sys.argv[3], 0.3))
    elif cmd == "mon":
        print(mon(g, " ".join(sys.argv[3:]), 0.5))
    elif cmd == "status":
        print("running:", running(g))
    elif cmd == "stop":
        if running(g):
            print(mon(g, "quit", 0.5))
        print("stopped")
    else:
        print("unknown command", cmd)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
