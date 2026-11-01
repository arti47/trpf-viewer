# Photo facade array (ambientCG CC0 Facade sets, 1K-JPG): python3 -I tools/fac-build.py <dir with F001/ F005/ ...> tex
# Output tex/fac.webp = 1024 x (1024*6) vertical strip, RGB = colour (sRGB), A = 0.5 + 0.5 x window/glass mask (roughness < 30/255).
# Layers: 0 F001 dark glass curtain wall, 1 F005 green glass, 2 F006 ribbon office, 3 F017 fins, 4 F019A punched stone, 5 F015 fine grid.
import sys, glob, numpy as np
from PIL import Image
src, out = sys.argv[1], sys.argv[2]
L = ['F001', 'F005', 'F006', 'F017', 'F019A', 'F015']
S = 1024; strip = Image.new('RGBA', (S, S * len(L)))
for i, n in enumerate(L):
    c = Image.open(glob.glob(f'{src}/{n}/*_Color.jpg')[0]).convert('RGB').resize((S, S), Image.LANCZOS)
    r = np.asarray(Image.open(glob.glob(f'{src}/{n}/*_Roughness.jpg')[0]).convert('L').resize((S, S), Image.BILINEAR), float)
    a = Image.fromarray((128 + np.clip((40 - r) / 20, 0, 1) * 127).astype(np.uint8))   # mask in A as 128..255: never near 0, so browser premultiply/unpremultiply keeps the colour
    im = c.copy(); im.putalpha(a); strip.paste(im, (0, i * S))
    print(n, np.asarray(c, float).reshape(-1, 3).mean(0).round(1), (np.asarray(a) > 191).mean().round(2))
strip.save(f'{out}/fac.webp', 'WEBP', quality=82, method=6)
