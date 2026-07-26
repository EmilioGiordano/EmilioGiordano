"""
Generates the profile banner.

Two real computations, drawn together:

  1. A distance field measured outward from the letterforms of EMILIO GIORDANO.
     Iso-distance lines are extracted with marching squares, so the contours hug
     each glyph and then merge into one silhouette as they move away -- the name
     rendered as topography.

  2. A Dijkstra shortest path across the same grid with the glyphs as obstacles,
     from the dot at bottom-left to the ring at top-right. It threads through the
     space between the two words because that genuinely is the cheapest route.

Outputs banner-light.svg and banner-dark.svg next to this file.

    pip install numpy scipy contourpy matplotlib fonttools
    python banner.py

Set BANNER_FONT to point at Cascadia Code (SIL OFL 1.1) if it is not on the default path.
"""
import argparse
import heapq
import math
import os

import numpy as np
from contourpy import contour_generator
from matplotlib.path import Path as MplPath
from scipy import ndimage
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from fontTools.varLib.instancer import instantiateVariableFont

W, H = 1200, 230          # svg viewBox
CELL = 2.0                # grid resolution, svg units
GW, GH = int(W / CELL), int(H / CELL)

TEXT = "EMILIO GIORDANO"
FONT = os.environ.get("BANNER_FONT", r"C:\Windows\Fonts\CascadiaCode.ttf")  # variable, SIL OFL 1.1
WEIGHT = 700
FONT_PX = 78
TRACK = 0.20              # letterspacing, em
CLEARANCE = 9.0           # units of clear space the route keeps from the glyphs

# Ring distances grow as they move away from the letters, so the field is dense
# and dark against the type and opens up towards the edges.
RINGS = [round(6.0 + 3.4 * k + 0.9 * k ** 1.85, 1) for k in range(0, 24)]

PALETTES = {
    # backgrounds match GitHub's own canvas so the banner sits on the page
    # rather than on top of it
    "light": dict(paper="#FFFFFF", ink="#14110F", field="#14110F",
                  op_near=0.44, op_far=0.06, pen2="#C2410C"),
    "dark":  dict(paper="#0D1117", ink="#F0EEE9", field="#F0EEE9",
                  op_near=0.34, op_far=0.05, pen2="#FF6B3D"),
}


# --------------------------------------------------------------- glyph outlines
class PolyPen(BasePen):
    """Flattens glyph outlines to polygons in font units."""

    def __init__(self, glyphSet):
        super().__init__(glyphSet)
        self.contours = []
        self._cur = []

    def _moveTo(self, pt):
        self._cur = [pt]

    def _lineTo(self, pt):
        self._cur.append(pt)

    def _curveToOne(self, p1, p2, p3):
        p0 = self._cur[-1]
        for i in range(1, 17):
            t = i / 16
            u = 1 - t
            self._cur.append((
                u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
                u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1]))

    def _qCurveToOne(self, p1, p2):
        p0 = self._cur[-1]
        for i in range(1, 13):
            t = i / 12
            u = 1 - t
            self._cur.append((
                u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
                u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]))

    def _closePath(self):
        if len(self._cur) > 2:
            self.contours.append(self._cur)
        self._cur = []

    _endPath = _closePath


def wordmark():
    font = instantiateVariableFont(TTFont(FONT), {"wght": WEIGHT}, updateFontNames=False)
    upm = font["head"].unitsPerEm
    cmap = font.getBestCmap()
    glyphset = font.getGlyphSet()

    scale = FONT_PX / upm
    advance = font["hmtx"][cmap[ord("A")]][0] * scale + TRACK * FONT_PX
    x0 = (W - (advance * len(TEXT) - TRACK * FONT_PX)) / 2
    cap = getattr(font["OS/2"], "sCapHeight", 1400)
    baseline = H / 2 + cap * scale / 2

    contours, dparts = [], []
    for i, ch in enumerate(TEXT):
        if ch == " ":
            continue
        pen = PolyPen(glyphset)
        glyphset[cmap[ord(ch)]].draw(pen)
        ox = x0 + i * advance
        for c in pen.contours:
            pts = [(ox + px * scale, baseline - py * scale) for px, py in c]
            contours.append(pts)
            dparts.append("M" + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z")
    return contours, "".join(dparts)


def rasterise(contours):
    ys, xs = np.mgrid[0:GH, 0:GW]
    pts = np.column_stack([(xs.ravel() + 0.5) * CELL, (ys.ravel() + 0.5) * CELL])
    compound = MplPath.make_compound_path(*[MplPath(np.array(c)) for c in contours])
    return compound.contains_points(pts).reshape(GH, GW)


# ---------------------------------------------------------------------- dijkstra
NEIGHBOURS = [(dx, dy, math.hypot(dx, dy))
              for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)]


def dijkstra(blocked, source):
    dist = np.full((GH, GW), np.inf)
    prev = np.full((GH, GW, 2), -1, dtype=np.int32)
    sx, sy = source
    dist[sy, sx] = 0.0
    pq = [(0.0, sx, sy)]
    while pq:
        d, x, y = heapq.heappop(pq)
        if d > dist[y, x]:
            continue
        for dx, dy, w in NEIGHBOURS:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < GW and 0 <= ny < GH) or blocked[ny, nx]:
                continue
            nd = d + w * CELL
            if nd < dist[ny, nx]:
                dist[ny, nx] = nd
                prev[ny, nx] = (x, y)
                heapq.heappush(pq, (nd, nx, ny))
    return dist, prev


def trace(prev, target):
    x, y = target
    out = []
    while x >= 0:
        out.append(((x + 0.5) * CELL, (y + 0.5) * CELL))
        x, y = prev[y, x]
    return out[::-1]


def smooth(pts, passes=10):
    for _ in range(passes):
        nxt = [pts[0]]
        for i in range(1, len(pts) - 1):
            nxt.append(((pts[i - 1][0] + 2 * pts[i][0] + pts[i + 1][0]) / 4,
                        (pts[i - 1][1] + 2 * pts[i][1] + pts[i + 1][1]) / 4))
        nxt.append(pts[-1])
        pts = nxt
    return pts


def decimate(pts, tol=0.7):
    out = [pts[0]]
    for p in pts[1:-1]:
        if math.dist(p, out[-1]) >= tol:
            out.append(p)
    out.append(pts[-1])
    return out


# ---------------------------------------------------------------------- contours
def iso_lines(field, level):
    x = (np.arange(GW) + 0.5) * CELL
    y = (np.arange(GH) + 0.5) * CELL
    gen = contour_generator(x=x, y=y, z=field, name="mpl2014", corner_mask=True)
    return [s for s in gen.lines(level)[0] if s is not None and len(s) > 3]


# --------------------------------------------------------------------- svg output
def pts_attr(pts, prec=0):
    return " ".join(f"{x:.{prec}f},{y:.{prec}f}" for x, y in pts)


def build_svg(pal, ring_groups, route, wordmark_d, src, tgt, animate):
    plen = sum(math.dist(route[i], route[i + 1]) for i in range(len(route) - 1))

    bands = []
    for op, segs in ring_groups:
        body = "".join(f'<polyline points="{pts_attr(s)}"/>' for s in segs)
        bands.append(f'<g stroke-opacity="{op:.3f}">{body}</g>')

    # The animation only ever moves away from the resting state and back to it, so a
    # renderer that ignores the stylesheet still shows the finished drawing rather
    # than a blank one.
    css = ""
    if animate:
        css = (
            f"@keyframes trace{{from{{stroke-dashoffset:{plen:.0f}}}to{{stroke-dashoffset:0}}}}"
            f"@keyframes appear{{from{{opacity:0}}to{{opacity:1}}}}"
            f".route{{stroke-dasharray:{plen:.0f};stroke-dashoffset:0;"
            f"animation:trace 2.8s cubic-bezier(.45,0,.25,1) .35s backwards}}"
            f".goal{{animation:appear .5s ease 2.9s backwards}}"
            f"@media(prefers-reduced-motion:reduce){{"
            f".route,.goal{{animation:none}}}}"
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Emilio Giordano">
<title>Emilio Giordano</title>
<style>{css}</style>
<rect width="{W}" height="{H}" fill="{pal['paper']}"/>
<g fill="none" stroke="{pal['field']}" stroke-width="1.15" stroke-linecap="round" stroke-linejoin="round">
{"".join(bands)}
</g>
<circle cx="{src[0]:.1f}" cy="{src[1]:.1f}" r="4.2" fill="{pal['pen2']}"/>
<path class="route" d="M{pts_attr(route)}" fill="none" stroke="{pal['pen2']}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
<circle class="goal" cx="{tgt[0]:.1f}" cy="{tgt[1]:.1f}" r="5" fill="none" stroke="{pal['pen2']}" stroke-width="2.2"/>
<path d="{wordmark_d}" fill="{pal['ink']}"/>
</svg>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--static", action="store_true", help="omit animation (for review shots)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    contours, wm_d = wordmark()
    inside = rasterise(contours)

    # distance measured outward from the glyphs, in svg units
    field = ndimage.distance_transform_edt(~inside) * CELL

    # route: glyphs plus a clearance margin are impassable
    blocked = ndimage.binary_dilation(
        inside, ndimage.generate_binary_structure(2, 2),
        iterations=max(1, int(round(CLEARANCE / CELL))))

    src_g = (int(172 / CELL), GH - int(30 / CELL))
    tgt_g = (int(1028 / CELL), int(30 / CELL))
    _, prev = dijkstra(blocked, src_g)
    if prev[tgt_g[1], tgt_g[0]][0] < 0:
        raise SystemExit("target unreachable -- lower CLEARANCE")
    route = decimate(smooth(trace(prev, tgt_g)), 2.0)

    ring_groups = []
    n = len(RINGS)
    for i, lv in enumerate(RINGS):
        segs = [decimate(list(map(tuple, s_)), 2.2) for s_ in iso_lines(field, lv)]
        segs = [s_ for s_ in segs if len(s_) > 3]
        if not segs:
            continue
        t = i / max(1, n - 1)
        ring_groups.append((None, segs, t))

    src = ((src_g[0] + 0.5) * CELL, (src_g[1] + 0.5) * CELL)
    tgt = ((tgt_g[0] + 0.5) * CELL, (tgt_g[1] + 0.5) * CELL)

    out = args.out or os.path.dirname(os.path.abspath(__file__))
    os.makedirs(out, exist_ok=True)
    for name, pal in PALETTES.items():
        groups = [(pal["op_near"] + (pal["op_far"] - pal["op_near"]) * t, segs)
                  for _, segs, t in ring_groups]
        svg = build_svg(pal, groups, route, wm_d, src, tgt, animate=not args.static)
        with open(os.path.join(out, f"banner-{name}.svg"), "w", encoding="utf8") as f:
            f.write(svg)

    total = sum(len(s) for _, s, _ in ring_groups)
    print(f"rings {len(ring_groups)}  segments {total}  route {len(route)}pts "
          f"({'static' if args.static else 'animated'})")


if __name__ == "__main__":
    main()
