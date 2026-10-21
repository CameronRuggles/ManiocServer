#!/usr/bin/env python3
"""Inject absolute-pointer mouse events into the QEMU usb-tablet
from INSIDE the guest (root), via /dev/input/event*.

Usage: inject-mouse.py X Y [click]
Coordinates are framebuffer pixels (1280x800); the tablet's ABS
range is auto-read from the device (usually 0..32767)."""
import fcntl, glob, os, struct, sys, time

EV_SYN, EV_KEY, EV_ABS = 0, 1, 3
SYN_REPORT, BTN_LEFT, ABS_X, ABS_Y = 0, 0x110, 0, 1
EVENT = struct.Struct("llHHi")


def find_tablet():
    # The QEMU USB tablet exposes ABS_X/ABS_Y with large ranges.
    for path in sorted(glob.glob("/dev/input/event*")):
        try:
            fd = os.open(path, os.O_RDWR)
        except OSError:
            continue
        # EVIOCGABS(ABS_X): _IOR('E', 0x40+abs, struct input_absinfo(24B))
        buf = fcntl.ioctl(fd, 0x80184540, struct.pack("6i", 0, 0, 0, 0, 0, 0))
        _v, _min, mx, _f, _fl, _r = struct.unpack("6i", buf)
        if mx and mx > 1000:
            return fd, mx
        os.close(fd)
    raise SystemExit("no absolute tablet device found")


def send(fd, typ, code, value):
    os.write(fd, EVENT.pack(0, 0, typ, code, value))


def main():
    x, y = int(sys.argv[1]), int(sys.argv[2])
    click = len(sys.argv) > 3 and sys.argv[3] == "click"
    fd, mx = find_tablet()
    # scale x and y to the ABS range (assume square-ish mapping via max)
    sx = int(x * mx / 1279)
    sy = int(y * mx / 799)
    send(fd, EV_ABS, ABS_X, sx)
    send(fd, EV_ABS, ABS_Y, sy)
    send(fd, EV_SYN, SYN_REPORT, 0)
    time.sleep(0.15)
    if click:
        send(fd, EV_KEY, BTN_LEFT, 1)
        send(fd, EV_SYN, SYN_REPORT, 0)
        time.sleep(0.12)
        send(fd, EV_KEY, BTN_LEFT, 0)
        send(fd, EV_SYN, SYN_REPORT, 0)
    print("injected", x, y, "click" if click else "move", "absmax", mx)


if __name__ == "__main__":
    main()
