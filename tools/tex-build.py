#!/usr/bin/env python3
# Builds tex/*.webp for the UE5-lifelike pass (2026-11-01) from CC0 Poly Haven downloads (1k JPG maps).
# usage: python3 -I tools/tex-build.py <download dir with *_diff/_nor.jpg, *_leaves_diff/_alpha.jpg, sky.jpg> <out dir>
# Sources (polyhaven.com, CC0): sparse_grass, clean_asphalt, concrete_tiles_02, concrete_wall_008, painted_plaster_wall, gravel_concrete,
# bark_platanus, laminate_floor_02, forest_ground_04, granite_tile; leaves of island_tree_01, jacaranda_tree, pachira_aquatica_01;
# HDRI kloofendal_48d_partly_cloudy_puresky (tonemapped JPG). Water normal + palm frond are generated here.
import sys, math, random, json
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
Image.MAX_IMAGE_PIXELS = None
src, out = sys.argv[1], sys.argv[2]
S = 512
MATS = ['sparse_grass', 'clean_asphalt', 'concrete_tiles_02', 'concrete_wall_008', 'painted_plaster_wall', 'gravel_concrete',
        'bark_platanus', 'laminate_floor_02', 'forest_ground_04', 'granite_tile']
alb, nrm, mean = [], [], []
def load(p, mode='RGB'): return Image.open(p).convert(mode).resize((S, S), Image.LANCZOS)
for m in MATS:
    a = np.asarray(load(f'{src}/{m}_diff.jpg'), dtype=np.float32)
    if m == 'sparse_grass':   # greener (SG cow grass): pull hue toward green, keep structure
        l = a.mean(axis=2, keepdims=True); g = np.array([0.82, 1.08, 0.62]) * l; a = np.clip(0.45 * a + 0.55 * g, 0, 255)
    alb.append(a.astype(np.uint8)); mean.append([round(float(v) / 255, 4) for v in a.reshape(-1, 3).mean(0)])
    nrm.append(np.asarray(load(f'{src}/{m}_nor.jpg')))
# water normal (layer 10): tileable sum of directional waves with integer wave numbers
yy, xx = np.mgrid[0:S, 0:S] / S * 2 * math.pi
rng = np.random.default_rng(7); h = np.zeros((S, S)); dx = np.zeros((S, S)); dy = np.zeros((S, S))
for i in range(48):
    k = rng.integers(2, 26); th = rng.normal(0.0, 0.6); kx, ky = int(round(k * math.cos(th))), int(round(k * math.sin(th)))
    if kx == 0 and ky == 0: continue
    amp = 1.0 / (kx * kx + ky * ky) ** 0.85; ph = rng.uniform(0, 2 * math.pi); s = kx * xx + ky * yy + ph
    dx += -amp * kx * np.sin(s); dy += -amp * ky * np.sin(s)
sc = 0.9 / max(np.abs(dx).max(), np.abs(dy).max()); n = np.dstack([-dx * sc, -dy * sc, np.ones((S, S))]); n /= np.linalg.norm(n, axis=2, keepdims=True)
alb.append(np.full((S, S, 3), 128, np.uint8)); nrm.append(((n * 0.5 + 0.5) * 255).astype(np.uint8)); mean.append([0.5, 0.5, 0.5])
Image.fromarray(np.vstack(alb)).save(f'{out}/mat.webp', quality=82, method=6)
Image.fromarray(np.vstack(nrm)).save(f'{out}/nrm.webp', quality=88, method=6)
json.dump({'layers': MATS + ['water'], 'mean': mean}, open(f'{out}/mat.json', 'w'))
# leaf atlas 1024² (2×2 cells): 0 broadleaf cluster, 1 bipinnate (rain tree / flame tree), 2 palmate shrub, 3 palm frond
def sprites(name, minpx):
    d = Image.open(f'{src}/{name}_leaves_diff.jpg').convert('RGB'); a = Image.open(f'{src}/{name}_leaves_alpha.jpg').convert('L')
    A = np.asarray(a) > 128; from collections import deque
    seen = np.zeros_like(A); H, W = A.shape; out_ = []
    for y0 in range(0, H, 2):
        for x0 in range(0, W, 2):
            if A[y0, x0] and not seen[y0, x0]:
                q = deque([(y0, x0)]); seen[y0, x0] = 1; ys = [y0]; xs = [x0]
                while q:
                    y, x = q.popleft()
                    for v, u in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                        if 0 <= v < H and 0 <= u < W and A[v, u] and not seen[v, u]: seen[v, u] = 1; q.append((v, u)); ys.append(v); xs.append(u)
                b = (min(xs), min(ys), max(xs) + 1, max(ys) + 1)
                if len(ys) > minpx and len(ys) < 0.7 * (b[2] - b[0]) * (b[3] - b[1]):   # skip solid strips (bark/branch pieces in the atlas)
                    im = d.crop(b).convert('RGBA'); im.putalpha(a.crop(b)); out_.append(im)
    return out_
def cluster(sp, n, size, seed, dark=0.55, spread=0.42, rot_out=True):
    rnd = random.Random(seed); C = Image.new('RGBA', (S, S), (0, 0, 0, 0)); cx = cy = S / 2
    for i in range(n):
        a = rnd.random() * 2 * math.pi; r = spread * S * rnd.random() ** 0.8 * (0.8 + 0.25 * math.sin(a * 5 + seed) + 0.15 * math.sin(a * 11 + 2 * seed));   # ragged lobed outline
        x = cx + r * math.cos(a); y = cy + r * math.sin(a)
        L = rnd.choice(sp); k = size * (0.7 + 0.5 * rnd.random()) / max(L.size); im = L.resize((max(2, int(L.size[0] * k)), max(2, int(L.size[1] * k))), Image.LANCZOS)
        ang = (-math.degrees(a) - 90 + rnd.uniform(-35, 35)) if rot_out else rnd.uniform(0, 360); im = im.rotate(ang, expand=True, resample=Image.BICUBIC)
        t = i / n; f = dark + (1 - dark) * t   # back leaves darker (drawn first)
        rgb = Image.eval(im.convert('RGB'), lambda v, f=f: int(v * f)); im = Image.merge('RGBA', (*rgb.split(), im.split()[3]))
        C.alpha_composite(im, (int(x - im.size[0] / 2), int(y - im.size[1] / 2)))
    return C
def frond(seed):   # palm: drooping-free frond seen from above (rachis + paired leaflets)
    rnd = random.Random(seed); C = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(C); x0, y0, x1, y1 = 40, S / 2, S - 30, S / 2
    d.line([(x0, y0), (x1, y1)], fill=(112, 104, 60, 255), width=5)
    for i in range(46):
        t = 0.06 + 0.92 * i / 46; x = x0 + (x1 - x0) * t; L = 190 * math.sin(math.pi * (0.15 + 0.85 * t)) * (0.9 + 0.2 * rnd.random())
        for s in (-1, 1):
            a = math.radians(55 + 15 * rnd.random()); ex = x + L * math.cos(a) * 0.55; ey = y0 + s * L * math.sin(a); w = 4 + 3 * rnd.random()
            g = int(70 + 45 * rnd.random()); col = (int(g * 0.7), g + 22, int(g * 0.36), 255); w = 2.5 + 2 * rnd.random()
            mx, my = (x + ex) / 2 + s * 6, (y0 + ey) / 2; d.polygon([(x - w, y0), (mx - w, my), (ex, ey), (mx + w, my), (x + w, y0)], fill=col)
            d.line([(x, y0), (ex, ey)], fill=(int(g * 0.9), g + 40, int(g * 0.5), 255), width=1)
    return C.filter(ImageFilter.SMOOTH)
broad = sprites('island_tree_01', 2000); bip = sprites('jacaranda_tree', 6000); palm_ = sprites('pachira_aquatica_01', 6000)
cells = [cluster(broad, 420, 48, 1, spread=0.4), cluster(bip, 90, 150, 2, spread=0.38), cluster(palm_, 110, 90, 3, spread=0.4), frond(4)]
At = Image.new('RGBA', (2 * S, 2 * S)); [At.paste(c, ((i % 2) * S, (i // 2) * S)) for i, c in enumerate(cells)]
# colour bleed under transparent texels (no dark fringes once mip-mapped / bilinear-filtered)
arr = np.asarray(At).astype(np.float32); al = arr[..., 3:4] / 255; blur = np.asarray(At.convert('RGB').filter(ImageFilter.GaussianBlur(12))).astype(np.float32)
wb = np.asarray(Image.fromarray((al[..., 0] * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(12))).astype(np.float32)[..., None] / 255
fill = blur / np.maximum(wb, 1e-3); rgb = arr[..., :3] * al + np.clip(fill, 0, 255) * (1 - al)
Image.fromarray(np.dstack([rgb, arr[..., 3]]).astype(np.uint8), 'RGBA').save(f'{out}/leaf.webp', quality=86, method=6)
# photo cloud layer: upper hemisphere of the HDRI (equirect), 1024×256: R = cloud opacity, G = cloud shading (photo luminance), B = 0; photo sun azimuth in mat.json
sky = Image.open(f'{src}/sky.jpg').convert('RGB'); W2, H2 = sky.size; sky = sky.crop((0, 0, W2, H2 // 2)).resize((1024, 256), Image.LANCZOS)
q = np.asarray(sky).astype(np.float32) / 255; R, G, B = q[..., 0], q[..., 1], q[..., 2]; sat = (B - R) / np.maximum(B, 1e-3); lum = 0.2126 * R + 0.7152 * G + 0.0722 * B
srow = np.percentile(sat, 92, axis=1, keepdims=True); cl = np.clip((srow - sat) / np.maximum(srow - 0.04, 0.05), 0, 1)
el = (1 - (np.arange(256) + 0.5) / 256)[:, None]   # 1 at the top row (zenith) … 0 at the horizon
cl *= np.clip((el - 0.03) / 0.08, 0, 1); cl = np.clip((cl - 0.12) / 0.7, 0, 1)
lo, hi = np.percentile(lum[cl > 0.5], 3), np.percentile(lum[cl > 0.5], 99.5); sh = np.clip((lum - lo) / (hi - lo), 0, 1)
iy, ix = np.unravel_index(np.argmax(lum * (el > 0.2)), lum.shape)
Image.fromarray((np.dstack([cl, sh, np.zeros_like(cl)]) * 255).astype(np.uint8)).save(f'{out}/sky.webp', quality=90, method=6)
meta = json.load(open(f'{out}/mat.json')); meta['skySunU'] = round((ix + 0.5) / 1024, 4); json.dump(meta, open(f'{out}/mat.json', 'w'))
print(meta)
