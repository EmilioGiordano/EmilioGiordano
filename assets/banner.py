"""
Generates the profile banner.

The background is a lattice of dots numbered left to right, top to bottom. Every
dot whose number is prime is drawn larger: the Sieve of Eratosthenes, run over the
banner itself. Cells that fall under the type are skipped but still counted, so the
sequence stays honest rather than being resequenced around the hole in the middle.

The wordmark is Cascadia Code (SIL OFL 1.1) converted to outlines, so the banner
does not depend on a font being available wherever it is rendered.

Outputs banner-light.svg and banner-dark.svg next to this file.

    pip install numpy scipy matplotlib fonttools
    python banner.py

Set BANNER_FONT if Cascadia Code is not on the default path.
"""
import os

import numpy as np
from scipy import ndimage
from matplotlib.path import Path as MplPath
from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen
from fontTools.varLib.instancer import instantiateVariableFont

W, H = 1200, 204
FONT = os.environ.get("BANNER_FONT", r"C:\Windows\Fonts\CascadiaCode.ttf")

NAME, NAME_PX, NAME_TRACK = "EMILIO GIORDANO", 60, 0.18
ROLE, ROLE_PX, ROLE_TRACK = "SOFTWARE DEVELOPER", 15, 0.42

STEP = 21          # lattice pitch
CLEAR = 15         # space kept between the lattice and the type
R_PLAIN, R_PRIME = 1.15, 2.7

PALETTES = {
    # the backgrounds are GitHub's own canvas colours, so the banner sits on the
    # page instead of on top of it
    "light": dict(bg="#FFFFFF", ink="#14110F", dots="#14110F", op_plain=0.15, op_prime=0.34),
    "dark":  dict(bg="#0D1117", ink="#E9E6E1", dots="#E9E6E1", op_plain=0.15, op_prime=0.34),
}


class PolyPen(BasePen):
    """Flattens glyph outlines to polygons in font units."""

    def __init__(self, glyphset):
        super().__init__(glyphset)
        self.contours, self._cur = [], []

    def _moveTo(self, pt):
        self._cur = [pt]

    def _lineTo(self, pt):
        self._cur.append(pt)

    def _curveToOne(self, p1, p2, p3):
        p0 = self._cur[-1]
        for i in range(1, 17):
            t = i / 16; u = 1 - t
            self._cur.append((
                u**3*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0],
                u**3*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1]))

    def _qCurveToOne(self, p1, p2):
        p0 = self._cur[-1]
        for i in range(1, 13):
            t = i / 12; u = 1 - t
            self._cur.append((
                u*u*p0[0] + 2*u*t*p1[0] + t*t*p2[0],
                u*u*p0[1] + 2*u*t*p1[1] + t*t*p2[1]))

    def _closePath(self):
        if len(self._cur) > 2:
            self.contours.append(self._cur)
        self._cur = []

    _endPath = _closePath


_fonts = {}


def load(weight):
    if weight not in _fonts:
        _fonts[weight] = instantiateVariableFont(
            TTFont(FONT), {"wght": weight}, updateFontNames=False)
    return _fonts[weight]


def cap_height(size, weight):
    f = load(weight)
    return getattr(f["OS/2"], "sCapHeight", 1400) * size / f["head"].unitsPerEm


def centred_text(s, size, weight, track, baseline):
    """Returns (polygons, svg path data, width), centred on the canvas."""
    f = load(weight)
    scale = size / f["head"].unitsPerEm
    cmap, glyphs = f.getBestCmap(), f.getGlyphSet()
    advance = f["hmtx"][cmap[ord("A")]][0] * scale + track * size
    width = advance * len(s) - track * size
    x0 = (W - width) / 2

    polys, parts = [], []
    for i, ch in enumerate(s):
        if ch == " ":
            continue
        pen = PolyPen(glyphs)
        glyphs[cmap[ord(ch)]].draw(pen)
        ox = x0 + i * advance
        for c in pen.contours:
            pts = [(ox + px * scale, baseline - py * scale) for px, py in c]
            polys.append(pts)
            parts.append("M" + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z")
    return polys, "".join(parts), width


def lattice(is_clear):
    """Evenly centred dots. Numbering counts suppressed cells too."""
    nx, ny = W // STEP, H // STEP
    ox, oy = (W - (nx - 1) * STEP) / 2, (H - (ny - 1) * STEP) / 2

    limit = nx * ny + 2
    prime = np.ones(limit + 1, bool)
    prime[:2] = False
    for p in range(2, int(limit ** 0.5) + 1):
        if prime[p]:
            prime[p * p::p] = False

    n = 1
    for j in range(ny):
        for i in range(nx):
            x, y = ox + i * STEP, oy + j * STEP
            n += 1
            if is_clear(x, y):
                yield x, y, bool(prime[n])


def build(pal):
    name_cap = cap_height(NAME_PX, 700)
    role_cap = cap_height(ROLE_PX, 400)
    gap_rule, gap_role = 24, 20

    top = (H - (name_cap + gap_rule + gap_role + role_cap)) / 2
    name_base = top + name_cap
    rule_y = name_base + gap_rule
    role_base = rule_y + gap_role + role_cap

    name_polys, name_d, name_w = centred_text(NAME, NAME_PX, 700, NAME_TRACK, name_base)
    role_polys, role_d, role_w = centred_text(ROLE, ROLE_PX, 400, ROLE_TRACK, role_base)

    # distance to the nearest glyph, sampled on a 2px grid
    cell = 2.0
    gw, gh = int(W / cell), int(H / cell)
    ys, xs = np.mgrid[0:gh, 0:gw]
    probe_pts = np.column_stack([(xs.ravel() + .5) * cell, (ys.ravel() + .5) * cell])
    compound = MplPath.make_compound_path(
        *[MplPath(np.array(c)) for c in name_polys + role_polys])
    inside = compound.contains_points(probe_pts).reshape(gh, gw)
    dist = ndimage.distance_transform_edt(~inside) * cell

    rx0, rx1 = W / 2 - name_w / 2, W / 2 + name_w / 2
    lx0, lx1 = W / 2 - role_w / 2, W / 2 + role_w / 2
    role_mid = role_base - role_cap / 2

    def is_clear(x, y):
        # the role line is letterspaced widely enough that a per-glyph distance
        # test walks straight between the letters, so clear a band around it
        if lx0 - 16 < x < lx1 + 16 and abs(y - role_mid) < 17:
            return False
        if rx0 - 12 < x < rx1 + 12 and abs(y - rule_y) < CLEAR:
            return False
        return dist[min(int(y / cell), gh - 1), min(int(x / cell), gw - 1)] >= CLEAR

    plain, primes = [], []
    for x, y, is_prime in lattice(is_clear):
        r = R_PRIME if is_prime else R_PLAIN
        (primes if is_prime else plain).append(
            f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}"/>')

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{NAME}, {ROLE.lower()}">
<title>{NAME.title()}</title>
<rect width="{W}" height="{H}" fill="{pal['bg']}"/>
<g fill="{pal['dots']}" fill-opacity="{pal['op_plain']}">{"".join(plain)}</g>
<g fill="{pal['dots']}" fill-opacity="{pal['op_prime']}">{"".join(primes)}</g>
<line x1="{rx0:.0f}" y1="{rule_y:.0f}" x2="{rx1:.0f}" y2="{rule_y:.0f}" stroke="{pal['dots']}" stroke-opacity="0.26" stroke-width="1.2"/>
<path d="{name_d}" fill="{pal['ink']}"/>
<path d="{role_d}" fill="{pal['ink']}" fill-opacity="0.5"/>
</svg>
"""


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    for name, pal in PALETTES.items():
        path = os.path.join(here, f"banner-{name}.svg")
        with open(path, "w", encoding="utf8") as f:
            f.write(build(pal))
        print("wrote", os.path.basename(path))


if __name__ == "__main__":
    main()
