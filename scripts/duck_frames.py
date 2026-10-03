#!/usr/bin/env python3
"""Draws the flying astronaut duck frame by frame into assets/duck/.

Shapes are drawn supersampled, then scaled down onto a small fixed palette so the
result reads as light pixel art. generate.py only embeds the PNGs, so this one-off
tool is the only part that needs Pillow:

    python scripts/duck_frames.py
"""
import json
import math
import os

from PIL import Image, ImageChops, ImageDraw

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "duck")
FRAMES, FRAME_MS = 48, 50
TILT = math.radians(-10)  # nose up
ORIGIN = (76, 64)          # body centre on the 128px canvas
INK = (27, 23, 48)
COL = {
    "white": (255, 255, 255), "shade": (226, 229, 242), "shade2": (196, 201, 222),
    "orange": (255, 138, 31), "orange_d": (222, 94, 12),
    "beak": (255, 176, 46), "beak_d": (240, 124, 22),
    "pack": (91, 110, 224), "pack_l": (146, 165, 255), "pack_d": (60, 72, 172),
    "steel": (190, 197, 214), "steel_d": (122, 130, 154),
    "purple": (115, 85, 221), "green": (57, 211, 83), "green_d": (30, 120, 50),
    "pink": (255, 168, 190), "glass": (150, 205, 255),
    "f_core": (255, 252, 235), "f_in": (255, 222, 98), "f_mid": (255, 160, 30),
    "f_out": (255, 96, 58), "glow": (124, 92, 255),
}
FLAME_DIR = (-0.912, 0.41)  # local exhaust direction (back and slightly down)
NOZZLE_BASE = (-31.0, 10.0)


# ---------------------------------------------------------------- geometry
def bezier(p0, p1, p2, p3, n=14):
    pts = []
    for i in range(n + 1):
        t = i / n
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
        pts.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return pts


def ellipse(cx, cy, rx, ry, rot=0.0, n=64):
    c, s = math.cos(rot), math.sin(rot)
    return [(cx + rx * math.cos(a) * c - ry * math.sin(a) * s, cy + rx * math.cos(a) * s + ry * math.sin(a) * c)
            for a in (2 * math.pi * i / n for i in range(n))]


def rrect(cx, cy, w, h, r, n=6):
    pts = []
    for (qx, qy, a0) in ((w / 2 - r, -h / 2 + r, -90), (w / 2 - r, h / 2 - r, 0),
                         (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + qx + r * math.cos(a), cy + qy + r * math.sin(a)))
    return pts


def capsule(a, b, r, n=10):
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    pts = []
    for (p, a0) in ((b, ang - math.pi / 2), (a, ang + math.pi / 2)):
        for i in range(n + 1):
            t = a0 + math.pi * i / n
            pts.append((p[0] + r * math.cos(t), p[1] + r * math.sin(t)))
    return pts


def place(pts, origin, ang):
    c, s = math.cos(ang), math.sin(ang)
    return [(origin[0] + x * c - y * s, origin[1] + x * s + y * c) for x, y in pts]


def star(cx, cy, ro, ri):
    return [(cx + (ro if i % 2 == 0 else ri) * math.cos(math.radians(-90 + 36 * i)),
             cy + (ro if i % 2 == 0 else ri) * math.sin(math.radians(-90 + 36 * i))) for i in range(10)]


def teardrop(base, d, length, width, wobble, n=22):
    nx, ny = -d[1], d[0]
    left, right = [], []
    for i in range(n + 1):
        s = i / n
        cx = base[0] + d[0] * s * length + nx * wobble * s * s
        cy = base[1] + d[1] * s * length + ny * wobble * s * s
        hw = width * (1 - s) ** 0.85 * (1 + 0.18 * math.sin(math.pi * s))
        left.append((cx + nx * hw, cy + ny * hw))
        right.append((cx - nx * hw, cy - ny * hw))
    back = math.atan2(-d[1], -d[0])
    cap = [(base[0] + width * math.cos(back + math.pi / 2 - math.pi * i / 10),
            base[1] + width * math.sin(back + math.pi / 2 - math.pi * i / 10)) for i in range(11)]
    return left + right[::-1] + cap


# ---------------------------------------------------------------- painter
class Painter:
    def __init__(self, size, ss=4):
        self.k, self.ss, self.W = size / 128, ss, size * ss
        self.solid = Image.new("RGBA", (self.W, self.W), (0, 0, 0, 0))
        self.soft = Image.new("RGBA", (self.W, self.W), (0, 0, 0, 0))
        self.w = max(0.9, 1.25 * self.k)  # outline width in output pixels

    def P(self, p):
        c, s = math.cos(TILT), math.sin(TILT)
        x, y = p
        return ((x * c - y * s + ORIGIN[0]) * self.k * self.ss, (x * s + y * c + ORIGIN[1]) * self.k * self.ss)

    def mask(self, pts):
        m = Image.new("L", (self.W, self.W), 0)
        ImageDraw.Draw(m).polygon([self.P(p) for p in pts], fill=255)
        return m

    def stroke(self, pts, width, closed=True):
        m = Image.new("L", (self.W, self.W), 0)
        tp = [self.P(p) for p in pts]
        if closed:
            tp += tp[:2]
        ImageDraw.Draw(m).line(tp, fill=255, width=max(1, round(width * self.ss)), joint="curve")
        return m

    def fill(self, pts, color, outline=True, clip=None, soft=False, alpha=255):
        layer = self.soft if soft else self.solid
        m = self.mask(pts)
        if outline:
            o = ImageChops.lighter(m, self.stroke(pts, 2 * self.w))
            if clip:
                o = ImageChops.multiply(o, clip)
            layer.paste(INK + (255,), mask=o)
        if clip:
            m = ImageChops.multiply(m, clip)
        layer.paste(color + (alpha,), mask=m)
        return m

    def line(self, pts, color, width, clip=None, closed=False):
        m = self.stroke(pts, width * self.k if self.k < 1 else width, closed)
        if clip:
            m = ImageChops.multiply(m, clip)
        self.solid.paste(color + (255,), mask=m)


# ---------------------------------------------------------------- the duck
def frame(i, size):
    t = i / FRAMES
    tau = 2 * math.pi
    p = Painter(size)

    # flame: flickers on a few harmonics of the loop so it repeats seamlessly
    d = FLAME_DIR
    nozzle = (NOZZLE_BASE[0] + d[0] * 7, NOZZLE_BASE[1] + d[1] * 7)
    length = 27 + 4 * math.sin(tau * 4 * t) + 2 * math.sin(tau * 7 * t + 1.3) + 1.2 * math.sin(tau * 11 * t + 0.4)
    width = 6.0 + 0.6 * math.sin(tau * 5 * t + 0.7)
    wob = 1.8 * math.sin(tau * 3 * t)
    p.fill(teardrop(nozzle, d, length * 1.22, width * 1.5, wob * 1.2), COL["glow"], outline=False, soft=True, alpha=120)
    for fl, fw, key in ((1.0, 1.0, "f_out"), (.78, .8, "f_mid"), (.55, .58, "f_in"), (.3, .36, "f_core")):
        p.fill(teardrop(nozzle, d, length * fl, width * fw, wob * fl), COL[key], outline=False)

    # jetpack + nozzle
    pack = rrect(-27, -3, 16, 34, 7)
    pm = p.fill(pack, COL["pack"])
    p.fill(rrect(-25, 5, 16, 18, 6), COL["pack_d"], outline=False, clip=pm)
    p.fill(rrect(-30.5, -6, 3.2, 20, 1.6), COL["pack_l"], outline=False, clip=pm)
    on = (i // 6) % 2 == 0
    p.fill(ellipse(-24, -13, 1.7, 1.7), COL["green"] if on else COL["green_d"], outline=False, clip=pm)
    p.fill(ellipse(-24, -8, 1.7, 1.7), COL["orange_d"] if on else COL["orange"], outline=False, clip=pm)
    nx, ny = -d[1], d[0]
    b, e = NOZZLE_BASE, nozzle
    p.fill([(b[0] + nx * 4.5, b[1] + ny * 4.5), (e[0] + nx * 6, e[1] + ny * 6),
            (e[0] - nx * 6, e[1] - ny * 6), (b[0] - nx * 4.5, b[1] - ny * 4.5)], COL["steel"])
    p.fill([(e[0] - d[0] * 2 + nx * 5.7, e[1] - d[1] * 2 + ny * 5.7), (e[0] + nx * 6, e[1] + ny * 6),
            (e[0] - nx * 6, e[1] - ny * 6), (e[0] - d[0] * 2 - nx * 5.7, e[1] - d[1] * 2 - ny * 5.7)],
           COL["steel_d"], outline=False)

    # legs paddling in the air (far one first, darker)
    for k, (attach, phase, color) in enumerate((((-5, 17), math.pi, COL["orange_d"]), ((6, 18), 0.0, COL["orange"]))):
        a = math.radians(122 + 16 * math.sin(tau * 2 * t + phase))
        knee = (attach[0] + 11 * math.cos(a), attach[1] + 11 * math.sin(a))
        p.fill(capsule(attach, knee, 1.7), color)
        toe = a + math.radians(48 + 10 * math.sin(tau * 2 * t + phase + 0.8))
        foot = [(0, -2.2), (9, -5.2), (7.6, -1.6), (11, 0), (7.6, 1.6), (9, 5.2), (0, 2.2)]
        p.fill(place(foot, knee, toe), color)

    # body
    body = ellipse(0, 0, 27, 22)
    bm = p.fill(body, COL["white"])
    p.fill(ellipse(3, 13, 25, 12), COL["shade"], outline=False, clip=bm)
    p.fill(ellipse(11, 7, 5.4, 5.4), COL["purple"])
    p.fill(star(11, 7, 3.3, 1.35), COL["white"], outline=False)

    # wing, flapping three times per loop
    ang = math.radians(203 + 30 * math.sin(tau * 3 * t))
    wing_local = (bezier((0, -1), (4, -10), (16, -9), (23, 0))
                  + [(19, 2.2), (20.5, 3.6), (15.5, 4.6), (16.5, 6.2), (11, 6.8)]
                  + bezier((11, 6.8), (7, 7.4), (2, 7.2), (0, 6))[1:]
                  + bezier((0, 6), (-4, 5), (-4, 0), (0, -1))[1:-1])
    wing_local = [(x * 1.3, y * 1.3) for x, y in wing_local]
    wing = place(wing_local, (-2, -6), ang)
    wm = p.fill(wing, COL["white"])
    p.fill(place([(-6, 3.4), (40, 3.4), (40, 16), (-6, 16)], (-2, -6), ang), COL["shade"], outline=False, clip=wm)
    p.line(place([(15, 1.5), (24, 0.8)], (-2, -6), ang), INK, 0.9, clip=wm)
    p.line(place([(12, 5.0), (19.5, 4.9)], (-2, -6), ang), INK, 0.9, clip=wm)

    # collar, helmet glass (behind the head), head, beak
    p.fill(ellipse(17, -17, 11.5, 4.2, math.radians(-38)), COL["steel"])
    hc, hr = (24, -28), 24
    p.fill(ellipse(*hc, hr, hr), COL["glass"], outline=False, soft=True, alpha=45)
    hm = p.fill(ellipse(22, -27, 14.5, 14.5), COL["white"])
    p.fill(ellipse(24, -18, 13, 7), COL["shade"], outline=False, clip=hm)
    p.fill(ellipse(28.5, -21, 3.3, 2.1), COL["pink"], outline=False, clip=hm)
    blink = {39: 1.4, 40: 0.6, 41: 0.6, 42: 1.4}.get(i, 3.2)
    p.fill(ellipse(27, -30, 2.4, blink), INK, outline=False)
    if blink > 2:
        p.fill(ellipse(27.9, -31.3, 0.95, 0.95), COL["white"], outline=False)
    beak = ellipse(38.5, -23.6, 7.6, 4.1, math.radians(-8))
    km = p.fill(beak, COL["beak"])
    p.fill(ellipse(38.5, -20.6, 9, 2.6, math.radians(-8)), COL["beak_d"], outline=False, clip=km)
    p.line([(31.5, -23.0), (45.5, -24.5)], INK, 0.9, clip=km)

    # helmet rim, reflections and antenna
    p.line(ellipse(*hc, hr, hr), (225, 233, 255), 1.8, closed=True)
    p.line(ellipse(*hc, hr + 1.4, hr + 1.4), INK, 1.1, closed=True)
    arc = ([(hc[0] + 19 * math.cos(math.radians(a)), hc[1] + 19 * math.sin(math.radians(a))) for a in range(200, 256, 4)]
           + [(hc[0] + 16.2 * math.cos(math.radians(a)), hc[1] + 16.2 * math.sin(math.radians(a))) for a in range(252, 196, -4)])
    p.fill(arc, COL["white"], outline=False)
    p.fill(ellipse(hc[0] + 17.6 * math.cos(math.radians(266)), hc[1] + 17.6 * math.sin(math.radians(266)), 1.3, 1.3),
           COL["white"], outline=False)
    top = (hc[0] - 5, hc[1] - hr - 0.5)
    tip = (top[0] - 4.5, top[1] - 7.5)
    p.line([top, tip], INK, 2.6)
    p.line([top, tip], COL["steel"], 1.2)
    p.fill(ellipse(tip[0] - 0.6, tip[1] - 1.6, 2.6, 2.6), COL["green"] if (i // 12) % 2 else (140, 245, 150))

    return finish(p, size)


def finish(p, size):
    palette = [INK] + list(COL.values()) + [(225, 233, 255), (140, 245, 150)]
    solid = p.solid.resize((size, size), Image.BOX)
    alpha = solid.getchannel("A").point(lambda v: 255 if v >= 120 else 0)
    pal = Image.new("P", (1, 1))
    flat = [c for rgb in palette for c in rgb]
    pal.putpalette(flat + flat[:3] * (256 - len(palette)))
    rgb = solid.convert("RGB").quantize(palette=pal, dither=Image.Dither.NONE).convert("RGBA")
    rgb.putalpha(alpha)

    soft = p.soft.resize((size, size), Image.BOX)
    soft.putalpha(soft.getchannel("A").point(lambda v: 0 if v < 18 else 55 if v < 70 else 100 if v < 120 else 140))
    soft.alpha_composite(rgb)
    return soft


def main():
    meta = {"frames": FRAMES, "frame_ms": FRAME_MS}
    c, s = math.cos(TILT), math.sin(TILT)
    nozzle = (NOZZLE_BASE[0] + FLAME_DIR[0] * 7, NOZZLE_BASE[1] + FLAME_DIR[1] * 7)
    meta["nozzle"] = [round(nozzle[0] * c - nozzle[1] * s + ORIGIN[0], 2), round(nozzle[0] * s + nozzle[1] * c + ORIGIN[1], 2)]
    meta["exhaust_dir"] = [round(FLAME_DIR[0] * c - FLAME_DIR[1] * s, 3), round(FLAME_DIR[0] * s + FLAME_DIR[1] * c, 3)]
    meta["canvas"] = 128
    for name, size in (("big", 128), ("small", 64)):
        out = os.path.join(ROOT, name)
        os.makedirs(out, exist_ok=True)
        for i in range(FRAMES):
            img = frame(i, size).quantize(colors=96, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
            img.save(os.path.join(out, f"{i:02d}.png"), optimize=True)
    with open(os.path.join(ROOT, "meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
    print("wrote", FRAMES, "frames per size to", ROOT)


if __name__ == "__main__":
    main()
