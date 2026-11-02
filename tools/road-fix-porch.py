# Retrace the 2 drop-off porch loops (TY 2026-11-02 "render this properly"): Blk 33 porch 6 (loop round the round island W of ESS)
# and Blk 31A porch 6 (drive round the porch's E side by #100/102). Hand-traced kerb polygons in site px (site.jpg at 6x, +-0.5 m)
# replace the old mask inside ZONES (cleared), island disc removed; Gaussian 0.6 m inside the zones, 0.15 m elsewhere (old edges
# unchanged), 0.5 iso-line -> loops + trapezoids as tools/road-smooth.py. Usage: python3 -I tools/road-fix-porch.py geo.js (run once)
import sys, json, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd
from skimage import measure
from shapely.geometry import Polygon, LineString, box as sbox
from shapely.ops import unary_union
geo = sys.argv[1]; src = open(geo).read().split('\n')
def grab(n):
    for i, l in enumerate(src):
        if l.startswith('GEO.%s = ' % n): return i, json.loads(l[len('GEO.%s = ' % n):].rstrip().rstrip(';'))
iR, roads = grab('siteRoads'); iL, loops = grab('siteRoadLoops')
PX, SC, IW, IH, PAD = 0.225, 4, 1284, 1009, 12
W, H = (IW + 2 * PAD) * SC, (IH + 2 * PAD) * SC
im = Image.new('L', (W, H), 0); d = ImageDraw.Draw(im)
f = lambda x, y: ((x + PAD) * SC, (y + PAD) * SC)
for y0, y1, a0, a1, b0, b1 in roads: d.polygon([f(a0, y0), f(a1, y0), f(b1, y1), f(b0, y1)], fill=255)
ZONES = [[(265, 560), (400, 560), (400, 628), (265, 628)], [(908, 418), (1052, 418), (1052, 526), (908, 526)]]
HAND = [[(306.7, 571.5), (377.5, 576.5), (384.2, 577.7), (374.2, 623), (374, 669), (323, 656), (290, 643.5), (271.7, 637), (272.5, 635),
         (278.3, 620), (282.5, 606.7), (288.3, 590), (295, 580), (301, 574)],
        [(913, 436), (918, 431), (930, 428), (950, 428), (968, 433), (970, 434), (1006, 456), (1015, 462), (1027, 475), (1035, 490), (1039, 505),
         (1040.5, 520), (1041, 535), (997, 535), (997, 520), (995, 513), (990, 508), (980, 506.5), (956, 505), (935, 504.5), (926, 503), (918, 500),
         (930, 494), (939, 489), (941, 484), (940.5, 468), (934, 451), (929, 447), (920, 440)]]
ISLANDS = [(329.2, 608, 18.5)]
# 31A drive-thru (TY 2026-11-02 "there should be a drive thru"): ~4 m lane under the canopy W of the green strip, strip = island
HAND.append([(904, 441), (915, 433), (932, 446), (930, 450), (930, 485), (934, 490), (925, 503), (912, 500), (911, 488), (912, 452)])
STRIPS = [[(930, 448), (941, 451), (941.5, 486), (936, 489), (930, 486)]]
zi = Image.new('L', (W, H), 0); zd = ImageDraw.Draw(zi)
for z in ZONES: zd.polygon([f(*p) for p in z], fill=255); d.polygon([f(*p) for p in z], fill=0)
for h in HAND: d.polygon([f(*p) for p in h], fill=255)
for cx, cy, r in ISLANDS: d.ellipse([f(cx - r, cy - r), f(cx + r, cy + r)], fill=0)
for q in STRIPS: d.polygon([f(*p) for p in q], fill=0)
m = np.asarray(im, np.float32) / 255
# extend roads that touch the image border outward (edge replicate) so the border doesn't round them off
p0, p1 = PAD * SC + 2, PAD * SC + IW * SC - 3; q0, q1 = PAD * SC + 2, PAD * SC + IH * SC - 3
m[:, :p0] = m[:, p0:p0 + 1]; m[:, p1:] = m[:, p1 - 1:p1]; m[:q0, :] = m[q0:q0 + 1, :]; m[q1:, :] = m[q1 - 1:q1, :]
w = nd.gaussian_filter(np.asarray(zi, np.float32) / 255, 1.0 / PX * SC)
g = w * nd.gaussian_filter(m, 0.6 / PX * SC) + (1 - w) * nd.gaussian_filter(m, 0.15 / PX * SC)
cs = measure.find_contours(np.pad(g, 1), 0.5)
pl = []
for c in cs:
    P = Polygon([((cc - 1 + 0.5) / SC - PAD, (rr - 1 + 0.5) / SC - PAD) for rr, cc in c]).buffer(0)
    if P.area * PX * PX >= 12: pl.append(P)
pl.sort(key=lambda p: -p.area)
depth = [sum(1 for o in pl if o is not p and o.area > p.area and o.contains(p.representative_point())) for p in pl]
U = unary_union([p for p, k in zip(pl, depth) if k % 2 == 0])
holes = [p for p, k in zip(pl, depth) if k % 2 == 1]
if holes: U = U.difference(unary_union(holes))
U = U.intersection(sbox(0, 0, IW, IH)).buffer(0)
G = list(U.geoms) if U.geom_type == 'MultiPolygon' else [U]
dp = lambda ring: [[round(x, 2), round(y, 2)] for x, y in LineString(ring).simplify(0.03 / PX).coords][:-1]
newL = []
for p in G:
    if p.area * PX * PX < 25: continue
    newL.append(dp(list(p.exterior.coords)))
    for h in p.interiors:
        if Polygon(h).area * PX * PX >= 12: newL.append(dp(list(h.coords)))
# trapezoids
def iv(y):
    s = U.intersection(LineString([(-5, y), (IW + 5, y)])); out = []
    for q in (s.geoms if hasattr(s, 'geoms') else [s]):
        if q.is_empty or q.geom_type != 'LineString': continue
        xs = [c[0] for c in q.coords]; out.append((min(xs), max(xs)))
    return sorted(out)
tr = []
def row(y0, y1, dep=0):
    A, B = iv(y0 + 1e-4), iv(y1 - 1e-4)
    if len(A) == len(B) and all(a[1] > b[0] - 2 and b[1] > a[0] - 2 for a, b in zip(A, B)):
        tr.extend([y0, y1, a[0], a[1], b[0], b[1]] for a, b in zip(A, B) if max(a[1] - a[0], b[1] - b[0]) > 0.05)
    elif dep < 4: h = (y1 - y0) / 2; row(y0, y0 + h, dep + 1); row(y0 + h, y1, dep + 1)
    else: tr.extend([y0, y1, a[0], a[1], a[0], a[1]] for a in iv((y0 + y1) / 2) if a[1] - a[0] > 0.05)
for k in range(IH): row(k, k + 1)
tr.sort(key=lambda t: (t[0], t[2])); tol = 0.03 / PX; out = []; last = {}
for t in tr:
    key = (round(t[0], 6), round(t[2], 4), round(t[3], 4)); o = last.pop(key, None)
    if o is not None:
        y0, y1 = o[0], t[1]; ok = o[1] - o[0] < 40
        for e0, e1 in ((2, 4), (3, 5)):
            sl = (t[e1] - o[e0]) / (y1 - y0)
            if abs(o[e0] + sl * (o[1] - y0) - o[e1]) > tol: ok = False
        if ok:
            o[1], o[4], o[5] = t[1], t[4], t[5]; last[(round(o[1], 6), round(o[4], 4), round(o[5], 4))] = o; continue
    t = list(t); out.append(t); last[(round(t[1], 6), round(t[4], 4), round(t[5], 4))] = t
src[iR] = 'GEO.siteRoads = ' + json.dumps([[round(v, 2) for v in t] for t in out], separators=(',', ':')) + ';'
src[iL] = 'GEO.siteRoadLoops = ' + json.dumps(newL, separators=(',', ':')) + ';'
open(geo, 'w').write('\n'.join(src))
print('roads', len(roads), '->', len(out), 'loops', len(loops), '->', len(newL), 'area m2', round(U.area * PX * PX))
