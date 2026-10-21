#!/usr/bin/env python3
"""Drive the skeleton ISO in QEMU/KVM on the rig: boot live, run Calamares,
install to qcow2, reboot, expect a LUKS prompt. Evidence = screendumps (PNG)
+ qemu monitor interaction. Usage:
  qemu-drive.py boot-live    # boot ISO only, screenshot desktop
  qemu-drive.py install      # full flow (resumes state machine via step arg)
State is kept in ~/iso-build/test/ ; screenshots named by step.
This is interactive automation: run subcommands one at a time and INSPECT
the PNG between steps (keys sent are logged)."""
import os, socket, subprocess, sys, time, zlib, struct

WORK = os.path.expanduser("~/iso-build")
TEST = os.path.join(WORK, "test")
ISO = os.path.join(WORK, "onionhost-skeleton-amd64.iso")
DISK = os.path.join(TEST, "installed.qcow2")
MON = os.path.join(TEST, "mon.sock")
SHOTS = os.path.join(TEST, "shots")
OVMF_CODE = "/usr/share/OVMF/OVMF_CODE_4M.secboot.fd"
OVMF_VARS = os.path.join(TEST, "OVMF_VARS.fd")

def mon(cmd, wait=0.4):
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(MON); s.settimeout(5)
    try: s.recv(4096)
    except Exception: pass
    s.sendall((cmd + "\n").encode()); time.sleep(wait)
    out = b""
    try:
        while True:
            d = s.recv(4096)
            if not d: break
            out += d
    except Exception: pass
    s.close(); return out.decode(errors="replace")

def running():
    return os.path.exists(MON) and subprocess.run(
        ["pgrep", "-f", "qemu-system.*onionhost-test"],
        capture_output=True).returncode == 0

def start(disk_boot=False):
    os.makedirs(SHOTS, exist_ok=True)
    if not os.path.exists(OVMF_VARS):
        subprocess.run(["cp", "/usr/share/OVMF/OVMF_VARS_4M.fd", OVMF_VARS], check=True)
    if not os.path.exists(DISK):
        subprocess.run(["qemu-img", "create", "-f", "qcow2", DISK, "24G"], check=True)
    args = ["qemu-system-x86_64", "-name", "onionhost-test", "-machine", "q35,accel=kvm",
            "-cpu", "host", "-m", "4096", "-smp", "2",
            "-drive", f"if=pflash,format=raw,readonly=on,file={OVMF_CODE}",
            "-drive", f"if=pflash,format=raw,file={OVMF_VARS}",
            "-drive", f"file={DISK},if=virtio,format=qcow2",
            "-netdev", "user,id=n0,hostfwd=tcp:127.0.0.1:2222-:22", "-device", "virtio-net-pci,netdev=n0",
            "-vga", "virtio", "-display", "none", "-usb", "-device", "usb-tablet",
            "-monitor", f"unix:{MON},server,nowait", "-serial", "file:" + os.path.join(TEST, "serial.log")]
    if not disk_boot:
        args += ["-drive", f"file={ISO},media=cdrom,readonly=on,if=ide",
                 "-boot", "order=d,menu=on"]
    else:
        args += ["-boot", "order=c"]
    subprocess.Popen(args, stdout=open(os.path.join(TEST, "qemu.out"), "ab"),
                     stderr=subprocess.STDOUT, start_new_session=True)
    for _ in range(50):
        if os.path.exists(MON): break
        time.sleep(0.2)
    print("qemu started, monitor:", os.path.exists(MON))

def shot(name):
    ppm = os.path.join(TEST, "shot.ppm"); png = os.path.join(SHOTS, name + ".png")
    mon(f"screendump {ppm}", 1.0)
    with open(ppm, "rb") as f:
        magic = f.readline(); dims = f.readline()
        while dims.startswith(b"#"): dims = f.readline()
        maxv = f.readline(); data = f.read()
    w, h = map(int, dims.split())
    def chunk(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    raw = b"".join(b"\x00" + data[i*w*3:(i+1)*w*3] for i in range(h))
    pngdata = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
               + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))
    open(png, "wb").write(pngdata)
    print("shot:", png, f"{w}x{h}")
    return png

KEYMAP = {" ": "spc", "\n": "ret", "\t": "tab", "-": "minus", "_": "shift-minus",
          ".": "dot", "/": "slash", "@": "shift-2", "=": "equal",
          "|": "shift-backslash", "&": "shift-7", ">": "shift-dot",
          "~": "shift-grave", "'": "apostrophe", ";": "semicolon",
          ":": "shift-semicolon", ",": "comma", "(": "shift-9", ")": "shift-0",
          "[": "bracket_left", "]": "bracket_right", "*": "shift-8",
          "$": "shift-4", "!": "shift-1", "?": "shift-slash", "%": "shift-5",
          "#": "shift-3", '"': "shift-apostrophe", "\\": "backslash",
          "<": "shift-comma", "+": "shift-equal", "^": "shift-6", "`": "grave"}
def sendkey(k, hold=None):
    mon(f"sendkey {k}" + (f" {hold}" if hold else ""), 0.15)

def type_text(text):
    for ch in text:
        if ch.isupper():
            sendkey("shift-" + ch.lower())
        elif ch in KEYMAP:
            sendkey(KEYMAP[ch])
        elif ch.isalnum():
            sendkey(ch)
        else:
            raise ValueError(f"unmappable char {ch!r}")

def click(x, y):
    mon(f"mouse_move {x} {y}", 0.3)
    mon("mouse_button 1", 0.2)
    mon("mouse_button 0", 0.3)

def cmd(name):
    if name == "start-live":
        if running(): print("already running"); return
        start(disk_boot=False)
    elif name == "start-disk":
        if running(): print("already running"); return
        start(disk_boot=True)
    elif name == "stop":
        print(mon("quit", 0.5)); print("stopped")
    elif name == "shot":
        shot(sys.argv[2])
    elif name == "key":
        sendkey(sys.argv[2]); print("sent", sys.argv[2])
    elif name == "type":
        type_text(sys.argv[2]); print("typed")
    elif name == "sleep":
        time.sleep(float(sys.argv[2])); print("slept")
    elif name == "status":
        print("running:", running())
    else:
        print(__doc__)

if __name__ == "__main__":
    cmd(sys.argv[1] if len(sys.argv) > 1 else "status")
