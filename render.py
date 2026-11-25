"""Draw entry.png, the one-image summary of 24 Nov 2026, from the ledger in SOURCES.md.

Run with a Python that has Pillow:  python3 render.py [out.png]
Everything is drawn in code: no photos, no logos, no generated art.
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
S = 2                      # draw at 2048, then resize to 1024
W = H = 1024
FONTS = "/usr/share/fonts/opentype/urw-base35/"

INK, INK2, LAND = "#0E2B30", "#163C42", "#2D565B"
PANEL, TXT, MUTED, YEL, WHITE = "#EAF0F1", "#10191B", "#4A6064", "#F4C542", "#FFFFFF"
REG = {"Europe": "#4A86D0", "Middle East": "#E0873A", "Africa": "#4FA35F",
       "Americas": "#C24D86", "Asia-Pacific": "#2FA8A0"}
TAGS = ("REPORTED", "CLAIM")
FIELDS = ("conflict", "diplomacy", "economy", "health", "tech", "sport",
          "disaster", "climate", "justice", "politics")


# ---------- ledger ----------
def load_ledger(path=ROOT / "SOURCES.md"):
    stories, keys, times, drops = [], [], [], []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("- "):
            continue
        f = [p.strip() for p in line[2:].split(" | ")]
        kind = f[0][0]
        if kind in "LCB" and len(f) == 10:
            lat, lon = (float(v) for v in f[3].split(","))
            stories.append(dict(id=f[0], kind=kind, region=f[1], place=f[2], lat=lat, lon=lon,
                                field=f[4], tag=f[5], time=f[6], head=f[7], fact=f[8],
                                urls=[u.strip() for u in f[9].split(";")]))
        elif kind == "K":
            keys.append(dict(value=f[1], label=f[2], urls=f[3].split(";")))
        elif kind == "T":
            times.append(dict(time=f[1], place=f[2], what=f[3]))
        elif kind == "D":
            drops.append(dict(date=f[1], what=f[2]))
    for s in stories:  # self-check: the brief's rules for every printed story
        assert len(s["urls"]) >= 2 and all(u.startswith("http") for u in s["urls"]), s["id"]
        assert len(s["head"].split()) <= 8, (s["id"], s["head"])
        assert s["region"] in REG and s["tag"] in TAGS and s["field"] in FIELDS, s["id"]
    assert [s["kind"] for s in stories].count("L") == 3
    assert len({s["id"] for s in stories}) == len(stories)
    for k in keys:
        assert len(k["urls"]) >= 2, k
    return stories, keys, times, drops


# ---------- drawing helpers ----------
_fc = {}
def F(name, size):
    key = (name, size)
    if key not in _fc:
        file = {"nb": "NimbusSansNarrow-Bold.otf", "nr": "NimbusSansNarrow-Regular.otf",
                "sb": "NimbusSans-Bold.otf", "sr": "NimbusSans-Regular.otf"}[name]
        _fc[key] = ImageFont.truetype(FONTS + file, int(round(size * S)))
    return _fc[key]

OVER = []   # every string that does not fit its box; render fails if any

def tw(s, font):
    return font.getlength(s) / S

def wrap(s, font, width, max_lines, tag=""):
    words, lines, cur = s.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if tw(t, font) <= width or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    if len(lines) > max_lines or any(tw(l, font) > width for l in lines):
        OVER.append(f"{tag}: {len(lines)} lines > {max_lines} or too wide: {s!r}")
    return lines

def fit(s, font, width, tag=""):
    if tw(s, font) > width:
        OVER.append(f"{tag}: {tw(s, font):.0f} > {width:.0f}: {s!r}")
    return s

class Pen:
    def __init__(self, img):
        self.d = ImageDraw.Draw(img)
    def text(self, x, y, s, font, fill, anchor="la"):
        self.d.text((x * S, y * S), s, font=font, fill=fill, anchor=anchor)
    def lines(self, x, y, lines, font, fill, lh, bottom=None, tag=""):
        for i, l in enumerate(lines):
            self.text(x, y + i * lh, l, font, fill)
        if bottom is not None and lines:
            box = self.d.textbbox((x * S, (y + (len(lines) - 1) * lh) * S), lines[-1], font=font, anchor="la")
            if box[3] / S > bottom + 0.5:
                OVER.append(f"{tag}: last line ends at {box[3] / S:.1f} > panel bottom {bottom}")
    def rect(self, x0, y0, x1, y1, fill=None, outline=None, width=1, r=0):
        self.d.rounded_rectangle((x0 * S, y0 * S, x1 * S, y1 * S), radius=r * S, fill=fill,
                                 outline=outline, width=int(width * S))
    def circle(self, cx, cy, r, fill=None, outline=None, width=1):
        self.d.ellipse(((cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S), fill=fill,
                       outline=outline, width=int(width * S))
    def poly(self, pts, fill=None, outline=None, width=1):
        p = [(x * S, y * S) for x, y in pts]
        self.d.polygon(p, fill=fill, outline=outline, width=int(width * S))
    def line(self, pts, fill, width=1):
        self.d.line([(x * S, y * S) for x, y in pts], fill=fill, width=int(width * S), joint="curve")


# ---------- icons (one flat style, drawn in a 14-unit box) ----------
def icon(p, field, x, y, c, k=14):
    u = k / 14
    if field == "conflict":
        pts = []
        for i in range(16):
            r = 7 * u if i % 2 == 0 else 3 * u
            import math
            a = math.pi * 2 * i / 16
            pts.append((x + 7 * u + r * math.cos(a), y + 7 * u + r * math.sin(a)))
        p.poly(pts, fill=c)
    elif field == "diplomacy":
        p.rect(x, y + 1 * u, x + 9 * u, y + 7 * u, fill=c, r=2 * u)
        p.rect(x + 5 * u, y + 6 * u, x + 14 * u, y + 12 * u, outline=c, width=1.4 * u, r=2 * u)
    elif field == "economy":
        for i, h in enumerate((5, 8, 12)):
            p.rect(x + i * 5 * u, y + (14 - h) * u, x + i * 5 * u + 3.5 * u, y + 14 * u, fill=c)
    elif field == "health":
        p.rect(x + 5 * u, y, x + 9 * u, y + 14 * u, fill=c)
        p.rect(x, y + 5 * u, x + 14 * u, y + 9 * u, fill=c)
    elif field == "tech":
        p.rect(x + 3 * u, y + 3 * u, x + 11 * u, y + 11 * u, fill=c)
        for i in (4.5, 7, 9.5):
            p.line([(x + i * u, y), (x + i * u, y + 14 * u)], c, 1 * u)
            p.line([(x, y + i * u), (x + 14 * u, y + i * u)], c, 1 * u)
    elif field == "sport":
        p.circle(x + 7 * u, y + 7 * u, 6.5 * u, outline=c, width=1.6 * u)
        p.circle(x + 7 * u, y + 7 * u, 2.5 * u, fill=c)
    elif field == "disaster":
        p.poly([(x + 7 * u, y), (x + 14 * u, y + 13 * u), (x, y + 13 * u)], fill=c)
        p.rect(x + 6.3 * u, y + 4 * u, x + 7.7 * u, y + 9 * u, fill=PANEL)
        p.rect(x + 6.3 * u, y + 10 * u, x + 7.7 * u, y + 11.5 * u, fill=PANEL)
    elif field == "climate":
        p.rect(x + 5 * u, y, x + 9 * u, y + 10 * u, outline=c, width=1.5 * u, r=2 * u)
        p.circle(x + 7 * u, y + 11 * u, 3 * u, fill=c)
    elif field == "justice":
        p.line([(x + 7 * u, y), (x + 7 * u, y + 13 * u)], c, 1.5 * u)
        p.line([(x + 1 * u, y + 3 * u), (x + 13 * u, y + 3 * u)], c, 1.5 * u)
        p.poly([(x, y + 8 * u), (x + 4 * u, y + 8 * u), (x + 2 * u, y + 4 * u)], fill=c)
        p.poly([(x + 10 * u, y + 8 * u), (x + 14 * u, y + 8 * u), (x + 12 * u, y + 4 * u)], fill=c)
        p.rect(x + 3 * u, y + 12.5 * u, x + 11 * u, y + 14 * u, fill=c)
    elif field == "politics":
        p.rect(x, y + 5 * u, x + 14 * u, y + 14 * u, fill=c)
        p.rect(x + 4 * u, y, x + 10 * u, y + 7 * u, fill=PANEL, outline=c, width=1.2 * u)


def tag_chip(p, x, y, tag, right=True):
    """Draw the tag chip ending at x (right-aligned); returns its width."""
    f = F("nb", 10)
    label = tag.capitalize()
    w = tw(label, f) + 10
    x0 = x - w if right else x
    if tag == "REPORTED":
        p.rect(x0, y, x0 + w, y + 14, fill=INK, r=7)
        p.text(x0 + 5, y + 2, label, f, WHITE)
    else:
        p.rect(x0, y, x0 + w, y + 14, fill=PANEL, outline="#C0561E", width=1.3, r=7)
        p.text(x0 + 5, y + 2, label, f, "#C0561E")
    return w


# ---------- lead scenes (each in its own sub-canvas) ----------
def scene_riyadh(w, h):
    import math
    im = Image.new("RGB", (w * S, h * S), "#13323A")
    p = Pen(im)
    for i in range(12):  # dusk sky bands
        p.rect(0, i * h / 12, w, (i + 1) * h / 12, fill=(19 + i * 3, 50 + i * 2, 58 + i))
    p.rect(0, h - 14, w, h, fill="#0B2025")
    towers = [(30, 40), (58, 58), (92, 34), (122, 50), (196, 46), (232, 62), (266, 38), (292, 54)]
    for x, hh in towers:
        p.rect(x, h - 14 - hh, x + 22, h - 14, fill="#1F4A52")
        for wy in range(int(h - 14 - hh + 6), int(h - 18), 8):
            for wx in (x + 4, x + 10, x + 16):
                p.rect(wx, wy, wx + 3, wy + 3, fill="#F4C542" if (wx + wy) % 3 else "#2E6A72")
    tx = 150  # the struck tower, generic (no real landmark shape)
    p.rect(tx, 18, tx + 30, h - 14, fill="#2B5E66")
    p.poly([(tx, 18), (tx + 15, 6), (tx + 30, 18)], fill="#2B5E66")
    for wy in range(26, h - 18, 7):
        p.rect(tx + 5, wy, tx + 25, wy + 3, fill="#3F7880")
    bx, by = tx + 24, 40  # impact
    pts = []
    for i in range(18):
        r = 17 if i % 2 == 0 else 7
        a = math.pi * 2 * i / 18
        pts.append((bx + r * math.cos(a), by + r * math.sin(a)))
    p.poly(pts, fill="#F08A2C")
    p.circle(bx, by, 6, fill="#FFE08A")
    for i in range(4):  # smoke
        p.circle(bx + 10 + i * 9, by - 10 - i * 6, 6 + i * 2, fill="#5B6E72")
    arc = [(w - 6 - t * (w - 6 - bx), 16 + 60 * (t - 0.5) ** 2 * -1 + 30 * t) for t in [i / 20 for i in range(18)]]
    for i in range(0, len(arc) - 1, 2):
        p.line([arc[i], arc[i + 1]], "#F4C542", 1.6)
    return im


def scene_poland(w, h):
    im = Image.new("RGB", (w * S, h * S), "#16384A")
    p = Pen(im)
    p.rect(0, h - 12, w, h, fill="#0D2430")
    # ministry building with columns and a white-red flag
    x0, x1 = 22, 150
    p.poly([(x0 - 6, 44), ((x0 + x1) / 2, 22), (x1 + 6, 44)], fill="#D9E2E4")
    p.rect(x0 - 4, 44, x1 + 4, 50, fill="#C5D0D3")
    for i in range(6):
        cx = x0 + 6 + i * 22
        p.rect(cx, 52, cx + 9, h - 18, fill="#D9E2E4")
    p.rect(x0 - 8, h - 18, x1 + 8, h - 12, fill="#C5D0D3")
    p.line([((x0 + x1) / 2, 22), ((x0 + x1) / 2, 4)], "#C5D0D3", 1.5)
    p.rect((x0 + x1) / 2, 4, (x0 + x1) / 2 + 18, 9, fill="#FFFFFF")
    p.rect((x0 + x1) / 2, 9, (x0 + x1) / 2 + 18, 14, fill="#D4213D")
    # the summons: a large diplomatic letter with a red seal (no missile art: the day's news is the protest)
    ex, ey, ew, eh = 190, 20, 110, 72
    p.rect(ex + 4, ey + 4, ex + ew + 4, ey + eh + 4, fill="#0D2430", r=4)
    p.rect(ex, ey, ex + ew, ey + eh, fill="#FFFFFF", r=4)
    p.line([(ex, ey), (ex + ew / 2, ey + eh * 0.55), (ex + ew, ey)], "#16384A", 2)
    p.line([(ex, ey + eh), (ex + ew * 0.4, ey + eh * 0.42)], "#C5D0D3", 1.4)
    p.line([(ex + ew, ey + eh), (ex + ew * 0.6, ey + eh * 0.42)], "#C5D0D3", 1.4)
    p.circle(ex + ew / 2, ey + eh * 0.55, 10, fill="#D4213D")
    p.circle(ex + ew / 2, ey + eh * 0.55, 5, outline="#F4A3B0", width=1.4)
    return im


def scene_ebola(w, h):
    import math
    im = Image.new("RGB", (w * S, h * S), "#173A35")
    p = Pen(im)
    p.rect(0, h - 12, w, h, fill="#0E2622")
    # one row of candidate-vaccine vials
    for c in range(6):
        x, y = 16 + c * 20, 52
        p.rect(x, y + 6, x + 12, y + 36, fill="#DCEFF2", r=2)
        p.rect(x, y + 20, x + 12, y + 36, fill="#7FC6D0", r=2)
        p.rect(x - 1, y, x + 13, y + 7, fill="#2FA8A0", r=1)
    # the purchase commitment: a signed document with a tick, not a jab (doses depend on trials)
    dx, dy = 140, 14
    p.rect(dx, dy, dx + 70, dy + 86, fill="#FFFFFF", r=3)
    for i in range(5):
        p.rect(dx + 9, dy + 12 + i * 10, dx + 61 - (i % 2) * 14, dy + 15 + i * 10, fill="#B8C6C9")
    p.line([(dx + 10, dy + 72), (dx + 18, dy + 66), (dx + 24, dy + 74), (dx + 34, dy + 64)], "#16384A", 1.6)
    p.line([(dx + 44, dy + 70), (dx + 50, dy + 77), (dx + 62, dy + 60)], "#4FA35F", 3)
    # filament virus: a long wavy thread with a closed loop (a crook shape reads as a "?")
    pts = []
    for i in range(48):
        t = i / 47
        pts.append((228 + 72 * t, 70 + 9 * math.sin(t * 14)))
    lx, ly_ = pts[-1]
    for i in range(30):
        a = -math.pi / 2 + 2 * math.pi * i / 29
        pts.append((lx + 10 * math.cos(a), ly_ - 10 + 10 * math.sin(a)))
    p.line(pts, "#E0873A", 5)
    for q in pts[::5]:
        p.circle(q[0], q[1], 1.3, fill="#FFD9A8")
    return im


SCENES = {"L1": scene_riyadh, "L2": scene_poland, "L3": scene_ebola}


# ---------- map ----------
LON0, LON1, LAT0, LAT1 = -130, 155, -40, 66
LANDS = [
    [(-165, 66), (-140, 70), (-90, 70), (-80, 64), (-75, 62), (-62, 58), (-56, 50), (-66, 45), (-70, 42), (-76, 37),
     (-81, 31), (-80, 25), (-84, 30), (-90, 29), (-97, 27), (-97, 22), (-92, 18), (-87, 21), (-88, 16), (-84, 11),
     (-79, 8), (-82, 8), (-86, 12), (-92, 14), (-105, 20), (-112, 29), (-117, 32), (-122, 37), (-124, 42),
     (-124, 48), (-130, 54), (-138, 59), (-150, 60), (-160, 58), (-165, 62)],
    [(-50, 60), (-42, 60), (-22, 68), (-30, 75), (-55, 75), (-60, 70)],
    [(-79, 8), (-72, 12), (-62, 10), (-52, 5), (-50, 0), (-35, -5), (-35, -10), (-39, -15), (-40, -22), (-48, -26),
     (-53, -34), (-58, -38), (-62, -40), (-65, -47), (-70, -52), (-75, -50), (-73, -40), (-71, -30), (-71, -18),
     (-76, -14), (-81, -6), (-80, 0), (-77, 4)],
    [(-10, 36), (-9, 43), (-2, 44), (-5, 48), (2, 51), (5, 53), (9, 57), (8, 58), (12, 56), (12, 54), (18, 55),
     (21, 57), (24, 60), (22, 61), (21, 64), (25, 70), (40, 68), (60, 70), (80, 72), (100, 74), (130, 72),
     (160, 70), (160, 62), (156, 57), (143, 52), (140, 46), (133, 43), (130, 42), (129, 36), (126, 34),
     (126, 38), (124, 40), (121, 39), (122, 31), (121, 28), (118, 24), (111, 21), (108, 17), (109, 12),
     (105, 9), (103, 10), (100, 13), (99, 8), (104, 1), (101, 3), (98, 8), (98, 16), (94, 17), (91, 22),
     (87, 21), (80, 15), (77, 8), (73, 17), (70, 22), (66, 25), (57, 26), (56, 24), (59, 22), (55, 17),
     (44, 12), (43, 15), (39, 21), (35, 28), (34, 30), (32, 31), (35, 33), (36, 36), (30, 37), (27, 37),
     (26, 40), (23, 40), (22, 37), (20, 40), (16, 42), (12, 44), (15, 40), (16, 38), (12, 42), (9, 44),
     (3, 43), (0, 39), (-2, 37), (-6, 36)],
    [(-17, 21), (-16, 28), (-10, 30), (-6, 36), (10, 37), (11, 33), (20, 31), (25, 32), (32, 31), (34, 28),
     (38, 18), (43, 12), (51, 12), (48, 5), (40, -3), (40, -11), (35, -20), (33, -26), (27, -34), (19, -35),
     (17, -29), (12, -17), (13, -8), (9, -1), (9, 4), (4, 6), (-8, 4), (-13, 8), (-17, 14)],
    [(44, -13), (50, -15), (47, -25), (44, -23)],
    [(114, -22), (122, -18), (130, -12), (137, -12), (142, -11), (146, -19), (153, -26), (151, -34), (146, -39),
     (138, -35), (131, -32), (115, -34)],
    [(95, 5), (106, -6), (102, -5)], [(109, 2), (117, 7), (119, 1), (116, -4), (110, -3)],
    [(130, 31), (135, 34), (140, 36), (142, 41), (140, 41), (136, 36), (130, 34)],
    [(-5, 50), (1, 51), (-2, 56), (-5, 58), (-6, 55)], [(120, 18), (122, 14), (126, 7), (122, 7)],
    [(131, -1), (141, -3), (150, -10), (141, -9)], [(120.5, 22.5), (121.9, 25), (121, 25.2), (120, 23)],
    [(-24, 64), (-14, 65), (-18, 66)], [(-85, 22), (-74, 20), (-77, 20), (-80, 23)],
]
SEAS = [
    [(28, 41), (28, 46), (33, 46), (35, 45), (38, 47), (41, 42), (36, 41)],
    [(47, 45), (53, 47), (54, 40), (50, 37), (49, 40)],
    [(10, 54), (14, 54), (20, 55), (23, 58), (30, 60), (22, 61), (18, 63), (22, 65), (17, 62), (18, 59),
     (16, 56), (11, 57)],
    [(-95, 58), (-80, 52), (-78, 62), (-90, 64)],
]
# Gulf/Europe pins sit 5-10 degrees apart; move them apart (px) so numbers stay legible
NUDGE = {"L2": (-8, -10), "C6": (9, -11), "C7": (-13, 5), "L1": (-2, 12), "C5": (11, -6), "C4": (13, 8)}

def draw_map(w, h, stories):
    im = Image.new("RGB", (w * S, h * S), INK2)
    p = Pen(im)
    def xy(lon, lat):
        return ((lon - LON0) / (LON1 - LON0) * w, (LAT1 - lat) / (LAT1 - LAT0) * h)
    for poly in LANDS:
        p.poly([xy(*q) for q in poly], fill=LAND)
    for poly in SEAS:
        p.poly([xy(*q) for q in poly], fill=INK2)
    for s in stories:   # briefs as small dots under the numbered pins
        if s["kind"] == "B":
            x, y = xy(s["lon"], s["lat"])
            p.circle(x, y, 2.2, fill=REG[s["region"]])
    for s in stories:
        if s["kind"] != "B":
            x, y = xy(s["lon"], s["lat"])
            dx, dy = NUDGE.get(s["id"], (0, 0))
            if dx or dy:   # leader line from the true spot to the moved pin
                p.circle(x, y, 1.6, fill=WHITE)
                p.line([(x, y), (x + dx, y + dy)], WHITE, 0.8)
            x, y = x + dx, y + dy
            r = 7.5 if s["kind"] == "L" else 6.5
            p.circle(x, y, r, fill=YEL if s["kind"] == "L" else REG[s["region"]], outline=INK, width=1)
            p.text(x, y + 0.3, str(int(s["id"][1:])), F("nb", 9 if s["kind"] == "L" else 8),
                   INK if s["kind"] == "L" else WHITE, anchor="mm")
    return im


# ---------- the page ----------
def render(out):
    stories, keys, times, drops = load_ledger()
    leads = [s for s in stories if s["kind"] == "L"]
    cards = [s for s in stories if s["kind"] == "C"]
    briefs = [s for s in stories if s["kind"] == "B"]
    counts = {r: sum(1 for s in stories if s["region"] == r) for r in REG}
    nreg = sum(1 for v in counts.values() if v)

    img = Image.new("RGB", (W * S, H * S), INK)
    p = Pen(img)

    # masthead: the day is the headline
    p.rect(16, 14, 98, 96, fill=YEL, r=6)
    p.text(57, 18, "TUE", F("nb", 16), INK, anchor="ma")
    p.text(57, 33, "24", F("nb", 44), INK, anchor="ma")
    p.text(57, 79, "NOV 2026", F("nb", 13), INK, anchor="ma")
    p.text(112, 8, fit("Tuesday, 24 November 2026", F("nb", 62), 896, "date"), F("nb", 62), YEL)
    dek = "The day's news: Houthi strike hits Riyadh; Poland summons Russia's envoy; Gavi moves to buy Ebola vaccine"
    p.text(112, 77, fit(dek, F("sr", 16), 896, "dek"), F("sr", 16), WHITE)

    # count bar
    p.rect(0, 108, W, 138, fill=INK2)
    lead_txt = f"{len(stories)} stories from {nreg} regions, all from 24 Nov 2026"
    p.text(16, 115, lead_txt, F("nb", 16), WHITE)
    x = 16 + tw(lead_txt, F("nb", 16)) + 18
    for r, c in REG.items():
        p.circle(x + 5, 124, 5, fill=c)
        lab = f"{r} {counts[r]}"
        p.text(x + 14, 116, lab, F("nb", 15), WHITE)
        x += 14 + tw(lab, F("nb", 15)) + 16
    if x > W - 16:
        OVER.append(f"count bar {x:.0f} > {W - 16}")
    x = 0
    for r, c in REG.items():
        seg = W * counts[r] / len(stories)
        p.rect(x, 135, x + seg, 138, fill=c)
        x += seg

    # leads
    lw, ly, lh = 324, 144, 280
    for i, s in enumerate(leads):
        x0 = 16 + i * (lw + 10)
        p.rect(x0, ly, x0 + lw, ly + lh, fill=PANEL, r=6)
        sc = SCENES[s["id"]](lw, 112)
        mask = Image.new("L", sc.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, sc.size[0], sc.size[1] + 12 * S), radius=6 * S, fill=255)
        img.paste(sc, (x0 * S, ly * S), mask)
        p.circle(x0 + 16, ly + 16, 11, fill=YEL, outline=INK, width=1.5)
        p.text(x0 + 16, ly + 16.5, str(i + 1), F("nb", 15), INK, anchor="mm")
        p.rect(x0, ly + 112, x0 + lw, ly + 116, fill=REG[s["region"]])
        cw = tag_chip(p, x0 + lw - 10, ly + 122, s["tag"])
        icon(p, s["field"], x0 + 12, ly + 122, REG[s["region"]], 13)
        p.text(x0 + 31, ly + 122, fit(f"{s['place']}, {s['field']}", F("nb", 14), lw - 50 - cw, s["id"]),
               F("nb", 14), MUTED)
        hl = wrap(s["head"], F("nb", 28), lw - 24, 3, s["id"])
        p.lines(x0 + 12, ly + 142, hl, F("nb", 28), TXT, 29)
        fy = ly + 142 + len(hl) * 29 + 6
        p.lines(x0 + 12, fy, wrap(s["fact"], F("sr", 14), lw - 24, 2, s["id"] + " fact"), F("sr", 14), MUTED, 17,
                bottom=ly + lh - 6, tag=s["id"])

    # key numbers
    ky = 430
    p.text(16, ky, "Key numbers, 24 Nov", F("nb", 12), YEL)
    kw = (W - 32) / len(keys)
    for i, k in enumerate(keys):
        x0 = 16 + i * kw
        if i:
            p.rect(x0 - 1, ky + 18, x0, ky + 60, fill="#2F5A60")
        p.text(x0 + 8, ky + 14, fit(k["value"], F("nb", 30), kw - 16, k["value"]), F("nb", 30), YEL)
        p.text(x0 + 8, ky + 47, fit(k["label"], F("nr", 12.5), kw - 14, k["label"]), F("nr", 12.5), WHITE)

    # cards: 3 columns x 4 rows
    cy0, cw_, ch, gx, gy = 500, 200, 111, 8, 6
    for j, s in enumerate(cards):
        x0 = 16 + (j % 3) * (cw_ + gx)
        y0 = cy0 + (j // 3) * (ch + gy)
        c = REG[s["region"]]
        p.rect(x0, y0, x0 + cw_, y0 + ch, fill=PANEL, r=5)
        p.rect(x0, y0, x0 + 4, y0 + ch, fill=c)
        p.circle(x0 + 17, y0 + 13, 8.5, fill=c)
        p.text(x0 + 17, y0 + 13.5, str(int(s["id"][1:])), F("nb", 11), WHITE, anchor="mm")
        icon(p, s["field"], x0 + 30, y0 + 7, c, 12)
        chip = tag_chip(p, x0 + cw_ - 6, y0 + 6, s["tag"])
        p.text(x0 + 46, y0 + 6, fit(s["place"], F("nb", 12), cw_ - 56 - chip, s["id"] + " place"), F("nb", 12), MUTED)
        hl = wrap(s["head"], F("nb", 19), cw_ - 18, 2, s["id"])
        p.lines(x0 + 11, y0 + 26, hl, F("nb", 19), TXT, 20)
        p.lines(x0 + 11, y0 + 26 + len(hl) * 20 + 4, wrap(s["fact"], F("sr", 12), cw_ - 18, 3, s["id"] + " fact"),
                F("sr", 12), MUTED, 14, bottom=y0 + ch - 4, tag=s["id"])

    # right column: map, timeline, briefs
    rx, rw = 642, 366
    p.text(rx, 500, "Where it happened: numbers match the stories", F("nb", 12), YEL)
    mp = draw_map(rw, 136, stories)
    img.paste(mp, (rx * S, 516 * S))
    ty = 658
    p.text(rx, ty, "Selected local times (UTC offset)", F("nb", 13), YEL)
    for i, t in enumerate(times):
        y = ty + 18 + i * 13
        p.text(rx, y, fit(t["time"], F("nb", 12), 108, t["time"]), F("nb", 12), YEL)
        p.text(rx + 112, y, fit(f"{t['place']}: {t['what']}", F("nr", 12), rw - 112, t["place"]), F("nr", 12), WHITE)
    by = ty + 18 + len(times) * 13 + 8
    p.text(rx, by, f"Also on 24 November ({len(briefs)} briefs)", F("nb", 13), YEL)
    half, BROW = (len(briefs) + 1) // 2, 18
    bw = (rw - 10) / 2
    for i, s in enumerate(briefs):
        x0 = rx + (i // half) * (bw + 10)
        y = by + 19 + (i % half) * BROW
        if s["tag"] == "CLAIM":
            p.circle(x0 + 4, y + 6, 3.4, outline=REG[s["region"]], width=1.6)
        else:
            p.circle(x0 + 4, y + 6, 3.6, fill=REG[s["region"]])
        p.text(x0 + 11, y, fit(s["head"], F("nr", 12), bw - 12, s["id"]), F("nr", 12), WHITE)
    brief_end = by + 19 + (half - 1) * BROW + 13   # bottom of the last brief line
    if brief_end > 960:
        OVER.append(f"briefs end at {brief_end:.0f} > 960")

    # footer: date check, legend, sources
    fy = 964
    p.rect(16, fy - 2, 556, H - 6, outline=YEL, width=1.2, r=4)
    p.text(24, fy + 2, "Date check: NOT this day's news, left out (real dates shown)", F("nb", 12), YEL)
    for i, d_ in enumerate(drops):
        x0 = 24 + (i % 2) * 268
        y = fy + 17 + (i // 2) * 11.5
        p.text(x0, y, fit(f"{d_['date']}: {d_['what']}", F("nr", 11), 262, d_["date"]), F("nr", 11), WHITE)
        if y + 12 > H - 7:
            OVER.append(f"date check row ends at {y + 12:.0f} > {H - 7}")
    lx = 568
    p.circle(lx + 4, fy + 8, 3.6, fill=WHITE)
    p.text(lx + 11, fy + 2, "Reported: named sources", F("nr", 11.5), WHITE)
    p.circle(lx + 146, fy + 8, 3.4, outline=WHITE, width=1.5)
    p.text(lx + 153, fy + 2, "Claim: one side, unverified", F("nr", 11.5), WHITE)
    foot = [
        "Every story here happened or was first reported on Tue 24 Nov 2026 (any time zone);",
        "each was checked in two outlets: AP, Reuters, AFP, BBC, Al Jazeera, Guardian,",
        "Anadolu, Yonhap, Xinhua, CNN and others. Full list in SOURCES.md.",
    ]
    for i, l in enumerate(foot):
        p.text(lx, fy + 17 + i * 12.5, fit(l, F("nr", 11), W - 16 - lx, "footer"), F("nr", 11), "#C9D6D8")

    if OVER:
        print("\n".join("OVER " + o for o in OVER))
        sys.exit(1)
    small = img.resize((W, H), Image.LANCZOS)
    small.save(out, optimize=True)
    print(f"wrote {out}: {len(stories)} stories, regions {counts}")


if __name__ == "__main__":
    render(sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "entry.png"))
