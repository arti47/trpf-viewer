# Rebuild the estate drive S of ESS / MSCP (porch 6 -> 31A drive) in geo.js (TY 2026-11-01 "roads here rendered wrong").
# The site.jpg grey mask broke it into 2 blobs under the tree canopies; here: grey component + hand south kerb band + linkway fill,
# same smoothing as the 2026-11-01 pass (close/open 1.9 m, holes < 60 m2, Gaussian 2 m, 0.5 iso), unioned with the other roads.
# Usage: python3 -I tools/road-fix-mscp.py geo.js site.jpg  (rewrites geo.js lines GEO.siteRoads / siteRoadLoops / siteLanes)
import sys, json, re, numpy as np
from PIL import Image
from scipy import ndimage as nd
from skimage import measure
from shapely.geometry import Polygon, LineString, MultiPolygon, box as sbox
from shapely.ops import unary_union
geo, img = sys.argv[1], sys.argv[2]
src = open(geo).read().split('\n')
def grab(name):
    for i, l in enumerate(src):
        if l.startswith('GEO.%s = ' % name): return i, json.loads(l[len('GEO.%s = ' % name):].rstrip().rstrip(';'))
iR, roads = grab('siteRoads'); iL, loops = grab('siteRoadLoops'); iN, lanes = grab('siteLanes')
PX = 0.225; SC = 4; X0, Y0, X1, Y1 = 230, 540, 900, 820
loopP = [Polygon(l).buffer(0) for l in loops]
# drop loops 1 (porch 6 / ESS blob) and 4 (blob S of MSCP); their trapezoids go too
drop = [i for i, P in enumerate(loopP) if P.bounds[0] > 250 and P.bounds[2] < 800 and P.bounds[1] > 560 and P.bounds[3] < 800]
assert len(drop) == 2, drop
def tcen(t): y0, y1, a0, a1, b0, b1 = t; return ((a0 + a1 + b0 + b1) / 4, (y0 + y1) / 2)
from shapely.geometry import Point
keep = [t for t in roads if not any(loopP[i].contains(Point(*tcen(t))) for i in drop)]
def tpoly(t): y0, y1, a0, a1, b0, b1 = t; return Polygon([(a0, y0), (a1, y0), (b1, y1), (b0, y1)]).buffer(0)
U1 = unary_union([tpoly(t) for t in keep])
# local mask (SC cells per px)
a = np.asarray(Image.open(img).convert('RGB')).astype(int)
mn, mx = a.min(2), a.max(2)
g = (mn > 205) & (mx - mn < 20) & (mx < 245)
lab, _ = nd.label(g)
comp = lab == lab[680, 500]
W, H = (X1 - X0) * SC, (Y1 - Y0) * SC
m = np.kron(comp[Y0:Y1, X0:X1], np.ones((SC, SC), bool))
from PIL import ImageDraw
def fill(poly):
    im = Image.new('1', (W, H), 0); ImageDraw.Draw(im).polygon([((x - X0) * SC, (y - Y0) * SC) for x, y in poly], fill=1)
    return np.asarray(im, bool)
# south kerb (plan verge edge, under the tree canopies) + band 5 m north of it, linkway crossing (x 775-805)
sk = [(272, 638), (400, 676.8), (644, 750), (694, 765), (745, 780), (770, 785), (790, 782.5), (805, 776.5), (818, 771.5)]
nb = []
for k in range(len(sk)):
    p = sk[max(k - 1, 0)]; q = sk[min(k + 1, len(sk) - 1)]; tx, ty = q[0] - p[0], q[1] - p[1]; L = np.hypot(tx, ty)
    nb.append((sk[k][0] + ty / L * 22, sk[k][1] - tx / L * 22))
m |= fill(sk + nb[::-1])
m |= fill([(772, 750), (806, 741), (814, 772), (782, 788)])
# 31A drive (kept loop 0 part) inside the window so the junction smooths
w = np.zeros((H, W), bool)
win = sbox(X0, Y0, X1, Y1)
for P in [loopP[0].intersection(sbox(760, 700, X1, 800))]:
    for q in (P.geoms if hasattr(P, 'geoms') else [P]):
        if q.geom_type == 'Polygon' and q.area > 1: w |= fill(list(q.exterior.coords))
m |= w
r = 1.9 / PX * SC
clo = nd.distance_transform_edt(nd.distance_transform_edt(~m) <= r) > r
clo = nd.distance_transform_edt(~(nd.distance_transform_edt(clo) > r)) <= r
hl, hn = nd.label(~clo)
for i in range(1, hn + 1):
    s = hl == i
    if s.sum() < 60 / (PX / SC) ** 2 and not (s[0].any() or s[-1].any() or s[:, 0].any() or s[:, -1].any()): clo |= s
f = nd.gaussian_filter(clo.astype(float), 2 / PX * SC)
cs = measure.find_contours(np.pad(f, 1), 0.5)
polys = []
for c in cs:
    pts = [(X0 + (cc - 1 + 0.5) / SC, Y0 + (rr - 1 + 0.5) / SC) for rr, cc in c]
    P = Polygon(pts).buffer(0)
    if P.area > 50: polys.append(P)
N = unary_union(polys)
# outer shapes = shells, holes subtract (orientation-agnostic: a contour inside another is a hole)
shells = [p for p in polys if not any(o is not p and o.contains(p) for o in polys)]
holes = [p for p in polys if p not in shells]
N = unary_union(shells).difference(unary_union(holes)) if holes else unary_union(shells)
N = N.intersection(sbox(X0 + 2, Y0 + 2, X1 - 2, Y1 - 2))
# window edge: only keep the new road piece (S of the blocks): the comp/band area; clip off anything E of the 31A junction
N = N.intersection(Polygon([(240, 560), (900, 690), (900, 800), (240, 800)]).union(sbox(240, 560, 420, 700)))
N = N.difference(loopP[3].buffer(3))
U = unary_union([U1, N])
D = U.difference(U1).buffer(0)
# trapezoids for D (1 px rows, sub-px edges, subdivide where the run count changes)
def iv(P, y):
    s = P.intersection(LineString([(X0 - 10, y), (X1 + 10, y)]))
    out = []
    for q in (s.geoms if hasattr(s, 'geoms') else [s]):
        if q.is_empty or q.geom_type not in ('LineString',): continue
        xs = [c[0] for c in q.coords]; out.append((min(xs), max(xs)))
    return sorted(out)
tr = []
def row(y0, y1, depth=0):
    A, B = iv(D, y0 + 1e-4), iv(D, y1 - 1e-4)
    if len(A) == len(B) and all(a[1] > b[0] - 2 and b[1] > a[0] - 2 for a, b in zip(A, B)):
        for a, b in zip(A, B):
            if max(a[1] - a[0], b[1] - b[0]) > 0.08: tr.append([y0, y1, a[0], a[1], b[0], b[1]])
    elif depth < 4:
        h = (y1 - y0) / 2; row(y0, y0 + h, depth + 1); row(y0 + h, y1, depth + 1)
    else:
        for a in iv(D, (y0 + y1) / 2):
            if a[1] - a[0] > 0.08: tr.append([y0, y1, a[0], a[1], a[0], a[1]])
b = D.bounds
for k in range(int(np.floor(b[1])), int(np.ceil(b[3]))): row(k + 0.25, k + 1.25)
# merge straight runs (edges within 0.03 m)
tr.sort(key=lambda t: (t[0], t[2])); tol = 0.03 / PX; out = []
open_ = {}
for t in tr:
    hit = None
    for o in out[-60:]:
        if abs(o[1] - t[0]) < 1e-6 and abs(o[4] - t[2]) < 1e-6 and abs(o[5] - t[3]) < 1e-6:
            hit = o; break
    if hit:
        y0, y1 = hit[0], t[1]; ok = True
        for e0, e1 in ((2, 4), (3, 5)):
            sl = (t[e1] - hit[e0]) / (y1 - y0); mid = hit[e0] + sl * (hit[1] - y0)
            if abs(mid - hit[e1]) > tol: ok = False
        if ok and hit[1] - hit[0] < 40: hit[1] = t[1]; hit[4] = t[4]; hit[5] = t[5]; continue
    out.append(list(t))
newR = keep + out
newR.sort(key=lambda t: (t[0], t[2]))
# loops: replace dropped + the one merged into (largest overlapping)
def dp(ring, tol=0.06 / PX):
    return list(LineString(ring).simplify(tol, preserve_topology=False).coords)
Ugeoms = list(U.geoms) if U.geom_type == 'MultiPolygon' else [U]
NC = [p for p in Ugeoms if p.intersects(N)]
merged = [i for i, P in enumerate(loopP) if i not in drop and any(P.intersects(c) for c in NC) and P.area > 1]
# keep islands that are their own loops (inside a merged component)
newL = [l for i, l in enumerate(loops) if i not in drop and i not in merged]
for c in NC:
    newL.append([[round(x, 2), round(y, 2)] for x, y in dp(list(c.exterior.coords))[:-1]])
    for h in c.interiors:
        hp = Polygon(h)
        if hp.area * PX * PX < 25 or any(Polygon(l).buffer(0).intersection(hp).area > 0.8 * hp.area for l in newL[:-1]): continue
        newL.append([[round(x, 2), round(y, 2)] for x, y in dp(list(h.coords))[:-1]])
# lanes: drop lanes inside the dropped loops; new centre-line from E of porch 6 to the 31A lane (W end at x 852)
def inD(q): return sum(any(loopP[i].contains(Point(v[0], v[1])) for i in drop) for v in q) > len(q) / 2
keepN = [ln for ln in lanes if not inD(ln[1])]
j31 = [k for k, ln in enumerate(keepN) if abs(ln[1][0][0] - 852) < 1 and abs(ln[1][0][1] - 740) < 1][0]
Ub = U.boundary
cen = []
skl = LineString(sk)
for s in np.arange(skl.project(Point(400, 676.8)), skl.project(Point(818, 771.5)), 8):
    p = skl.interpolate(s); p2 = skl.interpolate(min(s + 1, skl.length)); p1 = skl.interpolate(max(s - 1, 0))
    tx, ty = p2.x - p1.x, p2.y - p1.y; L = np.hypot(tx, ty); nx, ny = ty / L, -tx / L
    seg = LineString([(p.x - nx * 6, p.y - ny * 6), (p.x + nx * 70, p.y + ny * 70)]).intersection(U)
    segs = [q for q in (seg.geoms if hasattr(seg, 'geoms') else [seg]) if q.length > 0]
    if not segs: continue
    q = min(segs, key=lambda q: q.distance(p)); c0, c1 = q.coords[0], q.coords[-1]
    cen.append([(c0[0] + c1[0]) / 2, (c0[1] + c1[1]) / 2, q.length * PX])
for _ in range(2):
    cen = [cen[0]] + [[(cen[k - 1][i] + 2 * cen[k][i] + cen[k + 1][i]) / 4 for i in range(3)] for k in range(1, len(cen) - 1)] + [cen[-1]]
cen = [c for c in cen if c[0] < 840]
L31 = keepN[j31]
L31[1] = [[round(c[0], 1), round(c[1], 1), round(c[2], 1)] for c in cen] + L31[1]
L31[0] = [0, L31[0][1]]
src[iR] = 'GEO.siteRoads = ' + json.dumps([[round(v, 2) for v in t] for t in newR], separators=(',', ':')) + ';'
src[iL] = 'GEO.siteRoadLoops = ' + json.dumps(newL, separators=(',', ':')) + ';'
src[iN] = 'GEO.siteLanes = ' + json.dumps(keepN, separators=(',', ':')) + ';'
open(geo, 'w').write('\n'.join(src))
print('roads', len(roads), '->', len(newR), 'loops', len(loops), '->', len(newL), 'lanes', len(lanes), '->', len(keepN), 'new area m2', round(D.area * PX * PX), 'dropped', drop, 'merged', merged)
