"""Contact sheet of the new files, with the surface strip tinted the way the client does it."""
import os, sys, glob
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = lambda p: os.path.join(HERE, 'content', p)

def shade(base, s):  # TextureProxy::shadePixel, per channel
    s = s.astype(float); out = np.repeat(base[None, None, :].astype(float), s.shape[0], 0).repeat(s.shape[1], 1)
    hi = s > 130; lo = s < 126
    a = np.minimum((s - 128) / 128, 1)[..., None]
    out = np.where(hi[..., None], (1 - a) * out + 255 * a, out)
    out = np.where(lo[..., None], out * (0.5 + s[..., None] / 128 * 0.5), out)
    return np.clip(out, 0, 255).astype(np.uint8)

strip = np.asarray(Image.open(C('textures/SurfacesStrip.png')).convert('L'))
sheet = Image.new('RGB', (1100, 700), (60, 60, 70)); d = ImageDraw.Draw(sheet)
for i, col in enumerate([(196, 40, 28), (13, 105, 172), (75, 151, 74), (245, 205, 47), (163, 162, 164), (27, 42, 52)]):
    t = Image.fromarray(shade(np.array(col), strip)).resize((96, 576), Image.NEAREST)
    sheet.paste(t, (10 + i * 104, 10))
cur = sorted(glob.glob(C('textures/*Cursor.png')))
for i, f in enumerate(cur):
    im = Image.open(f).convert('RGBA'); x, y = 640 + (i % 6) * 72, 10 + (i // 6) * 84
    bg = Image.new('RGBA', (64, 64), (120, 160, 120, 255)); bg.alpha_composite(im); sheet.paste(bg.convert('RGB'), (x, y))
    d.text((x, y + 66), os.path.basename(f)[:-10], fill=(255, 255, 255))
ex = Image.open(C('textures/explosion.png')).convert('RGBA'); bg = Image.new('RGBA', ex.size, (40, 40, 60, 255)); bg.alpha_composite(ex)
sheet.paste(bg.convert('RGB'), (640, 440))
fp = Image.open(os.path.join(HERE, 'build/comics.fnt.preview.png')).resize((256, 128))
sheet.paste(fp.convert('RGB'), (790, 440))
sheet.save(os.path.join(HERE, 'build/preview.png')); print('ok')
