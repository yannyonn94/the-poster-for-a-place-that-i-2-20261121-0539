#!/usr/bin/env python3
"""Velmara — a travel poster for a place that does not exist.

Renders a 1024x1024 PNG travel poster for Velmara, a fictional white
cliff town above a luminous turquoise lagoon at golden dusk. Its
landmark is the Spiral Lighthouse: a white tower ringed with lanterns,
whose beam sweeps the lagoon as lantern boats drift home.

Pure standard library (zlib + struct for the PNG encoder, math for the
drawing). No network, no files read, fully deterministic: the same
bytes come out every run.

Usage:  python3 main.py
Writes: $MAKEFUN_OUTPUT_DIR/entry.png  (default /output/entry.png)
"""

import math
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
SKY_TOP = (43, 27, 78)        # deep dusk violet
SKY_MID = (122, 62, 120)      # rose violet
SKY_LOW = (232, 138, 90)      # peach at the horizon
SUN_CORE = (255, 214, 130)
SUN_HALO = (255, 178, 102)
SEA_TOP = (31, 168, 160)      # luminous turquoise
SEA_DEEP = (10, 84, 106)
MOUNT_FAR = (94, 58, 110)
MOUNT_NEAR = (66, 40, 84)
CLIFF = (122, 74, 62)         # warm rock
CLIFF_DARK = (74, 44, 48)
TOWN_WHITE = (245, 237, 224)
ROOF = (198, 96, 58)
TOWER_WHITE = (250, 244, 230)
TOWER_BAND = (214, 92, 66)
LANTERN = (255, 198, 92)
CREAM = (255, 243, 214)       # title
TITLE_SHADOW = (38, 20, 66)
CYPRESS = (28, 74, 58)
FOAM = (214, 244, 238)

# ---------------------------------------------------------------- canvas
# A flat RGB bytearray; every drawing primitive blends into it.


class Canvas:
    def __init__(self, w, h, fill=(0, 0, 0)):
        self.w, self.h = w, h
        self.px = bytearray(fill * (w * h))

    def put(self, x, y, rgb):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = rgb

    def blend(self, x, y, rgb, a):
        """Alpha-blend rgb over the pixel at (x, y); a in 0..1."""
        if 0 <= x < self.w and 0 <= y < self.h and a > 0:
            i = (y * self.w + x) * 3
            if a >= 1:
                self.px[i], self.px[i + 1], self.px[i + 2] = rgb
            else:
                for c in range(3):
                    self.px[i + c] = int(self.px[i + c] * (1 - a) + rgb[c] * a)

    def rect(self, x0, y0, x1, y1, rgb):
        x0, x1 = max(0, x0), min(self.w, x1)
        y0, y1 = max(0, y0), min(self.h, y1)
        for y in range(y0, y1):
            base = (y * self.w + x0) * 3
            row = bytes(rgb) * (x1 - x0)
            self.px[base:base + (x1 - x0) * 3] = row

    def hline(self, x0, x1, y, rgb):
        if 0 <= y < self.h:
            self.rect(max(0, x0), y, min(self.w, x1), y + 1, rgb)

    def disc(self, cx, cy, r, rgb, alpha=1.0):
        r2 = r * r
        for y in range(cy - r, cy + r + 1):
            dy = y - cy
            dx = int(math.sqrt(max(0, r2 - dy * dy)))
            for x in range(cx - dx, cx + dx + 1):
                self.blend(x, y, rgb, alpha)

    def ring(self, cx, cy, r, thick, rgb):
        for y in range(cy - r - thick, cy + r + thick + 1):
            for x in range(cx - r - thick, cx + r + thick + 1):
                d = math.hypot(x - cx, y - cy)
                if r - thick <= d <= r:
                    self.put(x, y, rgb)

    def line(self, x0, y0, x1, y1, rgb, width=1):
        steps = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for s in range(steps + 1):
            t = s / steps
            x = int(x0 + (x1 - x0) * t)
            y = int(y0 + (y1 - y0) * t)
            self.disc(x, y, width // 2 + 1, rgb)

    def poly(self, pts, rgb):
        """Scanline fill of a simple polygon."""
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                self.hline(int(xs[k]), int(xs[k + 1]), y, rgb)

    def vgrad(self, y0, y1, top, bottom):
        for y in range(y0, y1):
            t = (y - y0) / max(1, y1 - y0 - 1)
            rgb = tuple(int(top[c] + (bottom[c] - top[c]) * t) for c in range(3))
            self.hline(0, self.w, y, rgb)


def lerp(a, b, t):
    return tuple(int(a[c] + (b[c] - a[c]) * t) for c in range(3))


# ------------------------------------------------------- deterministic rng
_state = 1234567


def rnd():
    global _state
    _state = (_state * 1103515245 + 12345) & 0x7FFFFFFF
    return _state / 0x7FFFFFFF


# ------------------------------------------------------------------- font
# A bold 5x7 bitmap face, defined in-session. Only the letters of the
# place name are needed, plus nothing else — the name is the only text
# on the poster.
GLYPHS = {
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "A": ["..#..", ".#.#.", "#...#", "#...#", "#####", "#...#", "#...#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
}


def draw_text(cv, text, cx, y, scale, rgb, shadow=None):
    """Draw `text` centred on cx, top at y. Returns (width, height)."""
    cols = len(text) * 6 - 1
    w = cols * scale
    h = 7 * scale
    x0 = cx - w // 2
    for ch in text:
        g = GLYPHS[ch]
        for row in range(7):
            for col in range(5):
                if g[row][col] == "#":
                    bx = x0 + col * scale
                    by = y + row * scale
                    if shadow is not None:
                        cv.rect(bx + 5, by + 7, bx + scale + 5, by + scale + 7,
                                shadow)
                    cv.rect(bx, by, bx + scale, by + scale, rgb)
        x0 += 6 * scale
    return w, h


# ------------------------------------------------------------------ scene
def ridge_y(base, amp, freq, phase, x):
    return base + amp * math.sin(x * freq + phase) + 0.4 * amp * math.sin(
        x * freq * 2.7 + phase * 1.7)


def draw_scene(cv):
    # ---- sky: violet dusk down to a peach horizon ----------------------
    cv.vgrad(0, 470, SKY_TOP, SKY_MID)
    cv.vgrad(470, 600, SKY_MID, SKY_LOW)

    # ---- stars in the upper sky ----------------------------------------
    for _ in range(130):
        x = int(rnd() * W)
        y = int(rnd() * 330)
        a = 0.25 + 0.6 * rnd()
        if rnd() < 0.12:  # a few four-point sparkles
            cv.put(x, y, CREAM)
            cv.hline(x - 3, x + 4, y, (255, 243, 214))
            cv.line(x, y - 3, x, y + 3, (255, 243, 214))
        else:
            cv.blend(x, y, CREAM, a)

    # ---- low golden sun over the lagoon --------------------------------
    sx, sy = 300, 545
    for r, a in ((170, 0.06), (140, 0.08), (112, 0.11), (88, 0.15),
                 (68, 0.20)):
        cv.disc(sx, sy, r, SUN_HALO, a)
    cv.disc(sx, sy, 52, SUN_CORE)
    cv.disc(sx, sy, 44, (255, 226, 158))

    # ---- thin dusk clouds catching the peach light ----------------------
    # Broken dashes in a pre-mixed peach, so they read as cloud wisps
    # rather than ruled lines.
    for cy, cw in [(330, 300), (392, 380), (448, 220)]:
        cx = int(140 + rnd() * 480)
        for k in range(6):
            yy = cy + k * 4
            ww = int(cw * (1 - abs(k - 2.5) / 4))
            seg = cx - ww // 2
            while seg < cx + ww // 2:
                ln = int(24 + rnd() * 60)
                cv.hline(seg, min(seg + ln, cx + ww // 2), yy,
                         lerp(SKY_LOW, (255, 200, 160), 0.4))
                seg += ln + int(14 + rnd() * 34)

    # ---- birds: small dark chevrons over the lagoon ---------------------
    for bx, by, s in [(430, 380, 9), (480, 355, 7), (395, 420, 6),
                      (620, 330, 8), (660, 368, 6)]:
        cv.line(bx - s, by, bx, by - s // 2, (52, 30, 66), width=2)
        cv.line(bx, by - s // 2, bx + s, by, (52, 30, 66), width=2)

    # ---- far mountains --------------------------------------------------
    pts = [(0, 620)]
    for x in range(0, W + 32, 32):
        pts.append((x, int(ridge_y(540, 42, 0.006, 1.3, x))))
    pts.append((W, 620))
    cv.poly(pts, MOUNT_FAR)
    pts = [(0, 620)]
    for x in range(0, W + 32, 32):
        pts.append((x, int(ridge_y(575, 30, 0.009, 4.1, x))))
    pts.append((W, 620))
    cv.poly(pts, MOUNT_NEAR)

    # ---- lagoon ---------------------------------------------------------
    cv.vgrad(600, H, SEA_TOP, SEA_DEEP)

    # sun path: a bright golden column on the water under the sun,
    # widening as it runs toward the viewer, plus scattered glints
    for _ in range(140):
        x = int(sx + (rnd() - 0.5) * (90 + (rnd() * 300)))
        y = int(610 + rnd() * 340)
        ln = int(16 + rnd() * 52)
        a = 0.30 + 0.55 * rnd()
        for dx in range(ln):
            cv.blend(x + dx, y, SUN_CORE, a * (1 - dx / ln))
    for _ in range(90):
        x = int(sx + (rnd() - 0.5) * 260 * (0.4 + rnd()))
        y = int(610 + rnd() * 340)
        ln = int(14 + rnd() * 46)
        a = 0.28 + 0.5 * rnd()
        for dx in range(ln):
            cv.blend(x + dx, y, SUN_CORE, a * (1 - dx / ln))

    # wave strokes: pale dashes drifting across the lagoon
    for _ in range(160):
        x = int(rnd() * W)
        y = int(620 + rnd() * 380)
        ln = int(10 + rnd() * 34)
        cv.hline(x, x + ln, y, lerp(SEA_TOP, FOAM, 0.25 + 0.5 * rnd()))

    # ---- right headland: the cliff town of Velmara ----------------------
    # rocky headland rising from the sea
    cv.poly([(640, 1024), (700, 760), (790, 690), (880, 660), (960, 700),
             (1024, 760), (1024, 1024)], CLIFF)
    cv.poly([(700, 760), (790, 690), (880, 660), (960, 700), (1024, 760),
             (1024, 700), (900, 640), (760, 690)], CLIFF_DARK)

    # whitewashed houses cascading down the cliff
    houses = [
        (742, 716, 46, 40), (800, 700, 52, 44), (862, 694, 48, 40),
        (922, 712, 54, 42), (772, 758, 56, 44), (842, 748, 50, 42),
        (906, 762, 58, 46), (700, 800, 52, 40), (766, 812, 56, 44),
        (836, 806, 52, 42), (902, 818, 56, 44),
    ]
    for hx, hy, hw, hh in houses:
        cv.rect(hx, hy, hx + hw, hy + hh, TOWN_WHITE)
        # terracotta roof
        cv.poly([(hx - 4, hy), (hx + hw + 4, hy),
                 (hx + hw - 6, hy - 12), (hx + 6, hy - 12)], ROOF)
        # warm lit windows
        for wx in range(hx + 8, hx + hw - 8, 16):
            for wy in (hy + 10, hy + 26):
                if wy < hy + hh - 6:
                    cv.rect(wx, wy, wx + 7, wy + 9, LANTERN)

    # cypress trees between the houses
    for tx, ty, th in [(730, 700, 44), (880, 668, 52), (968, 700, 40),
                       (820, 726, 38)]:
        cv.disc(tx, ty - th // 2, 7, CYPRESS)
        cv.rect(tx - 2, ty - th, tx + 2, ty, (60, 40, 30))

    # cliff texture: warm rock strata and shaded cracks
    for _ in range(46):
        x = int(680 + rnd() * 330)
        y = int(700 + rnd() * 300)
        ln = int(12 + rnd() * 40)
        col = CLIFF_DARK if rnd() < 0.6 else (150, 98, 78)
        cv.hline(x, x + ln, y, col)
    # a pale path winding gently down the cliff to the quay
    for y in range(700, 990, 6):
        px = int(852 + 20 * math.sin(y * 0.021))
        cv.disc(px, y, 5, (232, 214, 186))
    # stone quay at the cliff base, with two lantern posts
    cv.rect(700, 968, 1024, 996, (96, 62, 58))
    cv.rect(700, 968, 1024, 974, (150, 104, 82))
    for qx in (760, 960):
        cv.rect(qx - 2, 936, qx + 2, 968, (40, 28, 52))
        cv.disc(qx, 930, 6, LANTERN)
        cv.disc(qx, 930, 12, SUN_HALO, 0.35)

    # ---- the Spiral Lighthouse ------------------------------------------
    lx, base_y = 872, 668
    # tapered white tower
    cv.poly([(lx - 26, base_y), (lx + 26, base_y), (lx + 15, 470),
             (lx - 15, 470)], TOWER_WHITE)
    # spiral band winding up the tower: horizontal stripes, each one
    # nudged a few pixels sideways, with the tower's tapered edges
    # re-drawn over them so the overhang reads as a spiral wrap
    for k in range(6):
        t0 = k / 6
        t1 = (k + 0.55) / 6
        y0 = int(base_y - (base_y - 470) * t0)
        y1 = int(base_y - (base_y - 470) * t1)
        w0 = 26 - (26 - 15) * t0
        w1 = 26 - (26 - 15) * t1
        nudge = 6 if k % 2 == 0 else -6
        cv.poly([(lx - w0 + nudge, y0), (lx + w0 + nudge, y0),
                 (lx + w1 + nudge, y1), (lx - w1 + nudge, y1)], TOWER_BAND)
    cv.line(lx - 26, base_y, lx - 15, 470, TOWER_WHITE, width=3)
    cv.line(lx + 26, base_y, lx + 15, 470, TOWER_WHITE, width=3)
    # lantern room: dark cap, glowing lamp, domed roof
    cv.rect(lx - 20, 440, lx + 20, 470, (40, 28, 52))
    cv.rect(lx - 12, 446, lx + 12, 466, LANTERN)
    cv.disc(lx, 456, 7, (255, 230, 160))
    cv.poly([(lx - 22, 440), (lx + 22, 440), (lx, 414)], (40, 28, 52))
    cv.disc(lx, 414, 4, LANTERN)
    # glow around the lamp
    cv.disc(lx, 456, 34, SUN_HALO, 0.22)
    cv.disc(lx, 456, 20, SUN_HALO, 0.30)

    # light beam sweeping left across the lagoon: a wide, soft cone
    # that fades as it runs, brightest at the lamp
    for y in range(448, 600):
        t = (y - 448) / 152
        xa = int(lx - 10 - (lx - 10 - 180) * t)
        xb = xa + int(26 + 90 * t)
        for x in range(xa, xb):
            a = 0.13 * (1 - t * 0.55)
            cv.blend(x, y, (255, 226, 158), a)

    # ---- lantern boats on the lagoon ------------------------------------
    for bx, by, s in [(330, 700, 1.0), (470, 790, 1.3), (210, 850, 0.8)]:
        bw = int(64 * s)
        bh = int(16 * s)
        cv.poly([(bx - bw // 2, by), (bx + bw // 2, by),
                 (bx + bw // 2 - 10, by + bh), (bx - bw // 2 + 10, by + bh)],
                (52, 32, 44))
        cv.line(bx - bw // 2 + 8, by - int(26 * s), bx - bw // 2 + 8, by,
                (52, 32, 44), width=2)
        cv.disc(bx - bw // 2 + 8, by - int(30 * s), 5, LANTERN)
        cv.disc(bx - bw // 2 + 8, by - int(30 * s), 9, SUN_HALO, 0.35)
        # lantern reflection on the water
        for k in range(1, 6):
            cv.hline(bx - bw // 2 + 4, bx - bw // 2 + 14, by + bh + k * 5,
                     LANTERN)

    # ---- foreground rocks, bottom left ----------------------------------
    cv.poly([(0, 1024), (0, 930), (120, 900), (240, 940), (300, 1024)],
            CLIFF_DARK)
    cv.poly([(0, 1024), (0, 970), (90, 950), (180, 980), (220, 1024)],
            (52, 30, 36))
    # a lantern post on the rocks
    cv.rect(96, 872, 102, 936, (40, 28, 52))
    cv.disc(99, 866, 7, LANTERN)
    cv.disc(99, 866, 14, SUN_HALO, 0.35)

    # ---- vintage poster frame -------------------------------------------
    cv.rect(0, 0, W, 10, CREAM)
    cv.rect(0, H - 10, W, H, CREAM)
    cv.rect(0, 0, 10, H, CREAM)
    cv.rect(W - 10, 0, W, H, CREAM)
    cv.rect(22, 22, W - 22, 26, CREAM)
    cv.rect(22, H - 26, W - 22, H - 22, CREAM)
    cv.rect(22, 22, 26, H - 22, CREAM)
    cv.rect(W - 26, 22, W - 22, H - 22, CREAM)

    # ---- the place name: the only text on the poster --------------------
    draw_text(cv, "VELMARA", W // 2, 96, 15, CREAM, shadow=TITLE_SHADOW)
    # small gold rule + diamond beneath the name
    cv.rect(W // 2 - 130, 232, W // 2 - 18, 236, LANTERN)
    cv.rect(W // 2 + 18, 232, W // 2 + 130, 236, LANTERN)
    cv.poly([(W // 2, 222), (W // 2 + 9, 234), (W // 2, 246),
             (W // 2 - 9, 234)], LANTERN)


# -------------------------------------------------------------------- png
def chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


def write_png(cv, path):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)  # filter: none
        base = y * cv.w * 3
        raw += cv.px[base:base + cv.w * 3]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "wb") as f:
        f.write(png)
    return len(png)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    path = os.path.join(out_dir, "entry.png")
    cv = Canvas(W, H)
    draw_scene(cv)
    size = write_png(cv, path)
    print(f"wrote {path} ({W}x{H}, {size} bytes)")


if __name__ == "__main__":
    main()
