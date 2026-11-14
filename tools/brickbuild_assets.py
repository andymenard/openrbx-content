"""Builds BrickBuild's own stand-in assets (all original, drawn/synthesized here) into assets/,
laid out like a classic client's content folder so places that refer to rbxasset:// paths find
something, and so the folder can be used anywhere those paths are expected. Also writes
src/client/builtin-assets.gen.ts so the client works standalone (bundled, lowest priority:
any asset folder the user adds wins).

    python3 tools/make_assets.py
"""
import base64, io, json, math, os, shutil, struct, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.join(os.path.dirname(__file__), '..')
OUT = os.path.join(ROOT, 'assets')
RNG = np.random.default_rng(7)

def path(p):
    full = os.path.join(OUT, p)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    return full

# ============================================================== meshes (format "version 1.00")
class Mesh:
    """Triangles with per-vertex normals and texture coordinates; UV rects index an atlas."""
    def __init__(self): self.tris = []  # [(p, n, uv) * 3]

    def tri(self, a, b, c, uvs, normals=None):
        if normals is None:
            n = np.cross(np.subtract(b, a), np.subtract(c, a)); l = np.linalg.norm(n)
            n = n / l if l else np.array([0, 1, 0]); normals = (n, n, n)
        self.tris.append(tuple(zip((a, b, c), normals, uvs)))

    def quad(self, a, b, c, d, rect):
        u0, v0, u1, v1 = rect
        self.tri(a, b, c, [(u0, v1), (u1, v1), (u1, v0)])
        self.tri(a, c, d, [(u0, v1), (u1, v0), (u0, v0)])

    def box(self, c, size, rect, basis=np.eye(3)):
        """Box centred at c; basis columns are its local x, y, z axes."""
        h = np.array(size) / 2; B = np.asarray(basis, float); c = np.asarray(c, float)
        P = lambda x, y, z: c + B @ (np.array([x, y, z]) * h)
        for ax in range(3):
            for s in (-1, 1):
                u, v = (ax + 1) % 3, (ax + 2) % 3
                def corner(a, b):
                    q = [0, 0, 0]; q[ax] = s; q[u] = a; q[v] = b; return P(*q)
                pts = [corner(-1, -1), corner(1, -1), corner(1, 1), corner(-1, 1)]
                if s < 0: pts = pts[::-1]
                self.quad(*pts, rect)

    def lathe(self, profile, rect, axis=1, center=(0, 0, 0), segs=16, smooth=True):
        """Surface of revolution: profile = [(radius, height), ...] along the axis."""
        c = np.asarray(center, float)
        def P(r, h, a):
            q = np.zeros(3); q[axis] = h
            u, v = (axis + 1) % 3, (axis + 2) % 3
            q[u] = r * math.cos(a); q[v] = r * math.sin(a); return c + q
        u0, v0, u1, v1 = rect
        for i in range(len(profile) - 1):
            (r0, h0), (r1, h1) = profile[i], profile[i + 1]
            for k in range(segs):
                a0, a1 = 2 * math.pi * k / segs, 2 * math.pi * (k + 1) / segs
                pa, pb, pc, pd = P(r0, h0, a0), P(r0, h0, a1), P(r1, h1, a1), P(r1, h1, a0)
                su0, su1 = u0 + (u1 - u0) * k / segs, u0 + (u1 - u0) * (k + 1) / segs
                sv0, sv1 = v1 - (v1 - v0) * i / (len(profile) - 1), v1 - (v1 - v0) * (i + 1) / (len(profile) - 1)
                if smooth:
                    dr, dh = r1 - r0, h1 - h0
                    def N(a):
                        q = np.zeros(3); q[axis] = -dr; u, v = (axis + 1) % 3, (axis + 2) % 3
                        q[u] = dh * math.cos(a); q[v] = dh * math.sin(a); l = np.linalg.norm(q) or 1; return q / l
                    na, nb = N(a0), N(a1)
                    # outward winding: counter-clockwise seen from outside
                    self.tri(pa, pb, pc, [(su0, sv0), (su1, sv0), (su1, sv1)], (na, nb, nb))
                    self.tri(pa, pc, pd, [(su0, sv0), (su1, sv1), (su0, sv1)], (na, nb, na))
                else:
                    self.tri(pa, pb, pc, [(su0, sv0), (su1, sv0), (su1, sv1)])
                    self.tri(pa, pc, pd, [(su0, sv0), (su1, sv1), (su0, sv1)])

    def sphere(self, c, r, rect, segs=16, rings=10):
        prof = [(r * math.sin(math.pi * i / rings), -r * math.cos(math.pi * i / rings)) for i in range(rings + 1)]
        self.lathe(prof, rect, 1, c, segs)

    def prism(self, outline, z0, z1, rect, axis_z=2):
        """Extruded convex polygon (outline in the plane across axis_z, counter-clockwise)."""
        def P(x, y, z):
            q = [0, 0, 0]; a, b = [i for i in range(3) if i != axis_z]; q[a] = x; q[b] = y; q[axis_z] = z; return np.array(q, float)
        if axis_z == 1: outline = outline[::-1]  # keep faces pointing outward in the (x, z) plane
        xs = [p[0] for p in outline]; ys = [p[1] for p in outline]
        uv = lambda x, y: (rect[0] + (rect[2] - rect[0]) * (x - min(xs)) / (max(xs) - min(xs) or 1),
                           rect[3] - (rect[3] - rect[1]) * (y - min(ys)) / (max(ys) - min(ys) or 1))
        for i in range(1, len(outline) - 1):
            A, B, C = outline[0], outline[i], outline[i + 1]
            self.tri(P(*A, z1), P(*B, z1), P(*C, z1), [uv(*A), uv(*B), uv(*C)])
            self.tri(P(*A, z0), P(*C, z0), P(*B, z0), [uv(*A), uv(*C), uv(*B)])
        for i in range(len(outline)):
            A, B = outline[i], outline[(i + 1) % len(outline)]
            self.quad(P(*A, z0), P(*B, z0), P(*B, z1), P(*A, z1), rect)

    def write(self, name):
        # version 1.00 stores positions at twice their size
        out = []
        for t in self.tris:
            for p, n, (u, v) in t:
                out.append('[%.4f,%.4f,%.4f][%.4f,%.4f,%.4f][%.4f,%.4f,0]' % (p[0] * 2, p[1] * 2, p[2] * 2, n[0], n[1], n[2], u, v))
        with open(path(name), 'w', newline='\n') as f:
            f.write('version 1.00\n%d\n%s' % (len(self.tris), ''.join(out)))

# ------------------------------------------------------------- atlases for the meshes
def atlas(name, regions, size=128):
    """regions: [(rect in 0..1, base rgb, kind)] -> PNG; kinds add a little texture."""
    img = Image.new('RGB', (size, size), (128, 128, 128)); px = img.load()
    for (u0, v0, u1, v1), rgb, kind in regions:
        x0, y0, x1, y1 = int(u0 * size), int(v0 * size), int(math.ceil(u1 * size)), int(math.ceil(v1 * size))
        for y in range(y0, y1):
            for x in range(x0, x1):
                t = (y - y0) / max(1, y1 - y0 - 1); s = (x - x0) / max(1, x1 - x0 - 1)
                k = 1.0
                if kind == 'metal': k = 0.8 + 0.35 * (1 - abs(2 * s - 1)) + RNG.normal(0, 0.02)
                elif kind == 'wood': k = 0.85 + 0.12 * math.sin(40 * s + 6 * math.sin(9 * t)) + RNG.normal(0, 0.03)
                elif kind == 'rubber': k = 0.9 + RNG.normal(0, 0.05)
                elif kind == 'paint': k = 0.92 + 0.1 * (1 - t) + RNG.normal(0, 0.015)
                elif kind == 'stripes': k = 0.75 if int(t * 6) % 2 else 1.05
                px[x, y] = tuple(max(0, min(255, int(c * k))) for c in rgb)
    img.save(path(name))

R = lambda i, n=4: (i % n / n + 0.01, i // n / n + 0.01, (i % n + 1) / n - 0.01, (i // n + 1) / n - 0.01)

def sword():
    m = Mesh()
    blade, guard, grip, pommel = R(0), R(1), R(2), R(3)
    m.prism([(-0.18, -1.0), (0.18, -1.0), (0.14, 1.55), (0, 2.0), (-0.14, 1.55)], -0.06, 0.06, blade, axis_z=1)
    m.box((0, 0, -1.1), (1.0, 0.22, 0.18), guard)
    m.lathe([(0.11, -1.95), (0.12, -1.6), (0.11, -1.2)], grip, axis=2, segs=10)
    m.sphere((0, 0, -2.02), 0.14, pommel, 10, 6)
    m.write('fonts/sword.mesh')
    atlas('textures/SwordTexture.png', [(blade, (205, 212, 222), 'metal'), (guard, (196, 160, 60), 'metal'),
                                        (grip, (92, 58, 34), 'wood'), (pommel, (196, 160, 60), 'metal')])

def rocketlauncher():
    m = Mesh()
    tube, rim, sight, grip = R(0), R(1), R(2), R(3)
    m.lathe([(0.5, -2.6), (0.5, 2.3)], tube, axis=0, segs=16)
    m.lathe([(0.56, 2.3), (0.56, 2.66), (0.42, 2.66), (0.42, -2.66), (0.56, -2.66), (0.56, -2.3)], rim, axis=0, segs=16)
    m.box((0.6, 0.62, 0), (0.9, 0.24, 0.24), sight)
    m.box((-0.3, -0.75, 0), (0.3, 0.6, 0.3), grip)
    m.box((0.9, -0.7, 0), (0.3, 0.5, 0.3), grip)
    m.write('fonts/rocketlauncher.mesh')
    atlas('textures/rocketlaunchertex.png', [(tube, (86, 110, 64), 'paint'), (rim, (170, 40, 30), 'paint'),
                                             (sight, (50, 50, 55), 'metal'), (grip, (40, 40, 40), 'rubber')])

def slingshot():
    m = Mesh()
    wood, band, pouch = R(0), R(1), R(2)
    m.lathe([(0.28, -2.4), (0.3, -1.0), (0.3, 0.2)], wood, axis=1, segs=10)
    for s in (-1, 1):
        a = math.atan2(1.3, 2.0) * s
        B = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
        m.box((s * 0.62, 1.1, 0), (0.5, 2.3, 0.5), wood, B)
    m.box((0, 2.05, 0.15), (2.6, 0.12, 0.12), band)
    m.box((0, 2.05, 0.35), (0.6, 0.35, 0.3), pouch)
    m.write('fonts/slingshot.mesh')
    atlas('textures/SlingshotTexture.png', [(wood, (140, 92, 48), 'wood'), (band, (180, 60, 50), 'rubber'), (pouch, (110, 80, 50), 'rubber')])

def paintballgun():
    m = Mesh()
    body, barrel, hopper, grip = R(0), R(1), R(2), R(3)
    m.box((0, -0.3, 0.1), (0.5, 1.4, 0.7), body)
    m.lathe([(0.16, 0.4), (0.16, 1.5), (0.2, 1.5), (0.2, 1.45)], barrel, axis=1, center=(0, 0, 0.2), segs=12)
    m.sphere((0, -0.3, 0.75), 0.42, hopper, 12, 8)
    a = 0.35
    m.box((0, -0.7, -0.55), (0.36, 0.4, 0.8), grip, np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]]))
    m.write('fonts/paintballgun.mesh')
    atlas('textures/PaintballGunTex128.png', [(body, (40, 90, 170), 'paint'), (barrel, (60, 60, 64), 'metal'),
                                              (hopper, (230, 200, 40), 'paint'), (grip, (30, 30, 30), 'rubber')])

def trowel():
    m = Mesh()
    wood, steel, blade = R(0), R(1), R(2)
    m.lathe([(0.15, -2.2), (0.2, -1.8), (0.19, -0.8), (0.14, -0.55)], wood, axis=1, segs=12)
    m.lathe([(0.12, -0.55), (0.12, -0.3)], steel, axis=1, segs=10)
    m.box((0, -0.15, 0), (0.08, 0.3, 0.08), steel)
    m.prism([(0, -0.05), (0.5, 0.7), (0, 2.2), (-0.5, 0.7)], -0.03, 0.03, blade, axis_z=2)
    m.write('fonts/trowel.mesh')
    atlas('textures/TrowelTexture.png', [(wood, (150, 96, 50), 'wood'), (steel, (120, 124, 130), 'metal'), (blade, (190, 196, 204), 'metal')])

def timebomb():
    m = Mesh()
    shell, cap, fuse = R(0), R(1), R(2)
    m.sphere((0, -0.05, 0), 0.95, shell, 18, 12)
    m.lathe([(0.32, 0.8), (0.32, 1.05), (0.0, 1.05)], cap, axis=1, segs=12)
    m.lathe([(0.05, 1.05), (0.05, 1.45)], fuse, axis=1, segs=6)
    m.write('fonts/timebomb.mesh')
    atlas('textures/bombtex.png', [(shell, (35, 35, 40), 'paint'), (cap, (140, 140, 140), 'metal'), (fuse, (200, 170, 110), 'stripes')])

# ============================================================== icons, decals, cursors
def canvas(n=64): return Image.new('RGBA', (n, n), (0, 0, 0, 0))
def outlined(d, shape, xy, fill, w=2, **kw):
    getattr(d, shape)(xy, fill=fill, outline=(20, 20, 20, 255), width=w, **kw)
def save(img, name, glow=False):
    if glow:
        a = img.split()[3].filter(ImageFilter.MaxFilter(3))
        base = Image.new('RGBA', img.size, (255, 255, 255, 0)); base.putalpha(a.point(lambda v: min(v, 150)))
        img = Image.alpha_composite(base, img)
    img.save(path(name))

def icons():
    S = 64
    # sword
    for name, n in (('textures/Sword128.png', 128), ('textures/sword.png', 64)):
        im = canvas(n); d = ImageDraw.Draw(im); k = n / 64
        outlined(d, 'polygon', [(14 * k, 46 * k), (44 * k, 10 * k), (54 * k, 8 * k), (52 * k, 18 * k), (18 * k, 50 * k)], (215, 220, 230, 255))
        outlined(d, 'polygon', [(8 * k, 40 * k), (12 * k, 36 * k), (28 * k, 52 * k), (24 * k, 56 * k)], (200, 165, 60, 255))
        d.line([(8 * k, 56 * k), (18 * k, 46 * k)], fill=(90, 60, 35, 255), width=int(6 * k))
        save(im, name)
    im = canvas(); d = ImageDraw.Draw(im)  # bomb
    outlined(d, 'ellipse', [10, 16, 50, 56], (40, 40, 45, 255)); outlined(d, 'rectangle', [24, 10, 36, 18], (150, 150, 150, 255))
    d.line([(30, 10), (38, 4)], fill=(210, 180, 110, 255), width=3); d.ellipse([36, 0, 44, 8], fill=(255, 190, 40, 255))
    d.ellipse([18, 24, 26, 32], fill=(110, 110, 120, 255)); save(im, 'textures/Bomb.png'); save(im, 'textures/bombicon.png')
    im = canvas(); d = ImageDraw.Draw(im)  # wall
    for r in range(5):
        for c in range(4):
            x = c * 16 - (8 if r % 2 else 0); outlined(d, 'rectangle', [x + 2, 8 + r * 10, x + 16, 16 + r * 10], (170, 70, 50, 255), w=1)
    save(im, 'textures/Wall.png')
    im = canvas(); d = ImageDraw.Draw(im)  # slingshot
    for pts in ([(30, 58), (30, 34)], [(30, 36), (16, 12)], [(30, 36), (44, 12)]):
        d.line(pts, fill=(20, 20, 20, 255), width=9); d.line(pts, fill=(150, 98, 52, 255), width=5)
    d.line([(16, 12), (30, 24), (44, 12)], fill=(190, 60, 50, 255), width=2); save(im, 'textures/Slingshot.png')
    im = canvas(); d = ImageDraw.Draw(im)  # rocket
    outlined(d, 'polygon', [(10, 54), (40, 24), (52, 12), (48, 30), (18, 60)], (220, 220, 225, 255))
    outlined(d, 'polygon', [(40, 24), (52, 12), (48, 30)], (200, 40, 30, 255))
    d.polygon([(10, 54), (4, 58), (8, 50)], fill=(255, 150, 30, 255)); save(im, 'textures/Rocket.png')
    im = canvas(); d = ImageDraw.Draw(im)  # superball
    outlined(d, 'ellipse', [12, 12, 52, 52], (60, 120, 230, 255)); d.ellipse([20, 18, 30, 28], fill=(200, 225, 255, 255))
    save(im, 'textures/Superball.png')
    im = canvas(); d = ImageDraw.Draw(im)  # game tool: pointer
    outlined(d, 'polygon', [(16, 8), (16, 50), (26, 40), (34, 58), (40, 55), (32, 38), (46, 38)], (255, 255, 255, 255))
    save(im, 'textures/GameTool.png')
    im = canvas(); d = ImageDraw.Draw(im)  # clone
    outlined(d, 'rectangle', [8, 22, 34, 48], (90, 160, 230, 255)); outlined(d, 'rectangle', [28, 12, 54, 38], (140, 200, 250, 255))
    d.line([(38, 44), (50, 44)], fill=(20, 20, 20, 255), width=3); d.line([(44, 38), (44, 50)], fill=(20, 20, 20, 255), width=3)
    save(im, 'textures/Clone.png')
    im = canvas(); d = ImageDraw.Draw(im)  # hammer
    outlined(d, 'polygon', [(26, 30), (32, 24), (56, 50), (50, 56)], (150, 100, 55, 255))
    outlined(d, 'polygon', [(10, 20), (26, 4), (40, 18), (24, 34)], (130, 135, 145, 255)); save(im, 'textures/Hammer.png')
    im = canvas(); d = ImageDraw.Draw(im)  # grab: open hand
    outlined(d, 'rounded_rectangle', [18, 28, 46, 56], (240, 200, 160, 255), radius=8)
    for i, x in enumerate((18, 25, 32, 39)):
        outlined(d, 'rounded_rectangle', [x, 10 + (i % 2) * 3, x + 7, 34], (240, 200, 160, 255), radius=3)
    outlined(d, 'rounded_rectangle', [44, 30, 54, 44], (240, 200, 160, 255), radius=4); save(im, 'textures/Grab.png')
    im = canvas(); d = ImageDraw.Draw(im)  # paintball
    outlined(d, 'rectangle', [10, 26, 44, 36], (40, 90, 170, 255)); outlined(d, 'rectangle', [44, 28, 58, 33], (60, 60, 64, 255))
    outlined(d, 'polygon', [(16, 36), (26, 36), (22, 54), (12, 54)], (30, 30, 30, 255)); outlined(d, 'ellipse', [22, 12, 38, 28], (230, 200, 40, 255))
    save(im, 'textures/PaintballIcon.png')
    im = canvas(); d = ImageDraw.Draw(im)  # medkit
    outlined(d, 'rounded_rectangle', [8, 16, 56, 52], (245, 245, 245, 255), radius=6)
    d.rectangle([27, 22, 37, 46], fill=(210, 30, 30, 255)); d.rectangle([20, 29, 44, 39], fill=(210, 30, 30, 255))
    save(im, 'textures/Medkit.png')
    im = canvas(); d = ImageDraw.Draw(im)  # laser
    outlined(d, 'rectangle', [6, 34, 30, 42], (90, 90, 100, 255)); d.line([(30, 38), (60, 20)], fill=(255, 40, 40, 255), width=3)
    d.line([(30, 38), (60, 20)], fill=(255, 200, 200, 255), width=1); save(im, 'textures/Laser.png')
    im = canvas(); d = ImageDraw.Draw(im)  # flamethrower
    outlined(d, 'rectangle', [6, 34, 30, 42], (170, 60, 40, 255))
    for i, c in enumerate(((255, 80, 20), (255, 150, 30), (255, 220, 80))):
        d.ellipse([30 + i * 6, 22 + i * 3, 58 - i * 2, 50 - i * 3], fill=c + (255,))
    save(im, 'textures/Flamethrower.png')
    im = canvas(); d = ImageDraw.Draw(im)  # multirocket
    for y in (14, 28, 42):
        outlined(d, 'polygon', [(8, y + 6), (44, y + 6), (56, y + 3), (44, y), (8, y)], (220, 220, 225, 255), w=1)
    save(im, 'textures/MultiRocket.png')
    im = canvas(); d = ImageDraw.Draw(im)  # rocket boots
    outlined(d, 'polygon', [(14, 8), (30, 8), (30, 40), (50, 40), (50, 52), (14, 52)], (120, 70, 40, 255))
    d.polygon([(18, 52), (26, 52), (22, 62)], fill=(255, 140, 30, 255)); d.polygon([(36, 52), (44, 52), (40, 62)], fill=(255, 140, 30, 255))
    save(im, 'textures/RocketBoots.png')
    im = canvas(); d = ImageDraw.Draw(im)  # super jump: spring
    for i in range(5): d.line([(18, 50 - i * 8), (46, 46 - i * 8)], fill=(150, 150, 160, 255), width=4)
    outlined(d, 'polygon', [(32, 2), (22, 14), (42, 14)], (80, 200, 80, 255)); save(im, 'textures/Super Jump.png')
    im = canvas(); d = ImageDraw.Draw(im)  # camera zoom
    outlined(d, 'ellipse', [8, 8, 40, 40], (200, 230, 255, 255), w=4); d.line([(36, 36), (56, 56)], fill=(20, 20, 20, 255), width=7)
    d.line([(16, 24), (32, 24)], fill=(20, 20, 20, 255), width=3); d.line([(24, 16), (24, 32)], fill=(20, 20, 20, 255), width=3)
    save(im, 'textures/CameraZoomIn.png')
    # seasonal set
    im = canvas(); d = ImageDraw.Draw(im)
    outlined(d, 'ellipse', [8, 16, 56, 56], (240, 130, 20, 255)); d.rectangle([28, 8, 34, 18], fill=(80, 120, 40, 255))
    d.polygon([(18, 30), (26, 30), (22, 24)], fill=(40, 20, 0, 255)); d.polygon([(38, 30), (46, 30), (42, 24)], fill=(40, 20, 0, 255))
    d.polygon([(18, 40), (46, 40), (40, 48), (24, 48)], fill=(40, 20, 0, 255)); save(im, 'textures/HalloweenPumpkin.png')
    im = canvas(); d = ImageDraw.Draw(im)
    outlined(d, 'polygon', [(14, 58), (14, 26), (20, 12), (32, 6), (44, 12), (50, 26), (50, 58), (42, 52), (32, 58), (22, 52)], (240, 240, 250, 230))
    d.ellipse([22, 22, 28, 30], fill=(20, 20, 20, 255)); d.ellipse([36, 22, 42, 30], fill=(20, 20, 20, 255)); save(im, 'textures/HalloweenGhost.png')
    im = canvas(); d = ImageDraw.Draw(im)
    outlined(d, 'ellipse', [12, 6, 52, 44], (235, 230, 215, 255)); outlined(d, 'rectangle', [20, 40, 44, 56], (235, 230, 215, 255))
    d.ellipse([19, 18, 29, 30], fill=(20, 20, 20, 255)); d.ellipse([35, 18, 45, 30], fill=(20, 20, 20, 255))
    for x in (24, 30, 36): d.line([(x, 44), (x, 56)], fill=(20, 20, 20, 255), width=2)
    save(im, 'textures/HalloweenSkull.png')
    im = canvas(); d = ImageDraw.Draw(im)
    outlined(d, 'polygon', [(10, 54), (40, 24), (52, 12), (48, 30), (18, 60)], (240, 130, 20, 255))
    d.polygon([(10, 54), (4, 58), (8, 50)], fill=(160, 60, 220, 255)); save(im, 'textures/HalloweenRocket.png')
    im = canvas(); d = ImageDraw.Draw(im)
    outlined(d, 'rectangle', [8, 22, 56, 58], (120, 115, 130, 255)); outlined(d, 'polygon', [(4, 24), (32, 6), (60, 24)], (80, 70, 90, 255))
    for x in (14, 28, 42): d.rectangle([x, 30, x + 8, 40], fill=(250, 230, 120, 255))
    save(im, 'textures/HalloweenAsylum.png')
    # studio tool icons
    # small tool icons: the window's own art when it is there - Tango (public domain) for the
    # two there is a word for, and BrickBuild's own glyphs for the three there is not
    window = {'color': 'tango/applications-graphics', 'freemove': 'app/tool-move',
              'material': 'app/part', 'resize': 'app/tool-size', 'surface': 'tango/x-office-drawing'}
    for n, col in (('color', (220, 80, 80)), ('freemove', (80, 160, 220)), ('material', (150, 120, 90)), ('resize', (90, 190, 90)), ('surface', (200, 180, 70))):
        src = os.path.join(ROOT, 'ui/icons/%s.png' % window[n])
        if os.path.exists(src): shutil.copy(src, path('icons/%s_sel.png' % n)); continue
        im = canvas(32); d = ImageDraw.Draw(im); outlined(d, 'rounded_rectangle', [3, 3, 28, 28], col + (255,), radius=5)
        d.rectangle([10, 10, 21, 21], outline=(255, 255, 255, 255), width=2); save(im, 'icons/%s_sel.png' % n)

def spawn_decal():
    n = 128; im = canvas(n); d = ImageDraw.Draw(im)
    d.ellipse([6, 6, n - 6, n - 6], outline=(255, 255, 255, 230), width=8)
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5; r = 44 if i % 2 == 0 else 19
        pts.append((n / 2 + r * math.cos(a), n / 2 + r * math.sin(a)))
    d.polygon(pts, fill=(255, 255, 255, 230)); save(im, 'textures/SpawnLocation.png')

def cursors():
    def arrow(name, col=(255, 255, 255, 255), far=False):
        im = canvas(); d = ImageDraw.Draw(im)
        d.polygon([(32, 32), (32, 52), (37, 47), (41, 56), (44, 54), (40, 45), (47, 45)], fill=col, outline=(0, 0, 0, 255))
        if far: d.ellipse([27, 27, 37, 37], outline=(0, 0, 0, 255), width=2)
        save(im, name)
    arrow('textures/ArrowCursor.png'); arrow('textures/ArrowFarCursor.png', (200, 200, 200, 255), True)
    for name, wait in (('textures/GunCursor.png', False), ('textures/GunWaitCursor.png', True)):
        im = canvas(); d = ImageDraw.Draw(im); col = (255, 60, 60, 255) if wait else (255, 255, 255, 255)
        for (a, b, c, e) in ((32, 18, 32, 27), (32, 37, 32, 46), (18, 32, 27, 32), (37, 32, 46, 32)):
            d.line([(a, b), (c, e)], fill=(0, 0, 0, 255), width=4); d.line([(a, b), (c, e)], fill=col, width=2)
        if wait: d.arc([22, 22, 42, 42], 0, 270, fill=col, width=2)
        save(im, name)
    def tool_cursor(name, draw):
        im = canvas(); d = ImageDraw.Draw(im); draw(d)
        d.polygon([(32, 32), (32, 42), (35, 39), (40, 40)], fill=(255, 255, 255, 255), outline=(0, 0, 0, 255)); save(im, name)
    tool_cursor('textures/GrabCursor.png', lambda d: outlined(d, 'rounded_rectangle', [36, 40, 52, 56], (240, 200, 160, 255), w=1, radius=4))
    tool_cursor('textures/GrabRotateCursor.png', lambda d: d.arc([36, 38, 56, 58], 30, 330, fill=(0, 0, 0, 255), width=3))
    tool_cursor('textures/HammerCursor.png', lambda d: (outlined(d, 'rectangle', [38, 40, 54, 46], (130, 135, 145, 255), w=1), d.line([(46, 46), (46, 58)], fill=(150, 100, 55, 255), width=3)))
    tool_cursor('textures/DragCursor.png', lambda d: [d.line(l, fill=(0, 0, 0, 255), width=2) for l in ([(46, 38), (46, 58)], [(36, 48), (56, 48)])])
    tool_cursor('textures/FillCursor.png', lambda d: outlined(d, 'polygon', [(38, 44), (50, 40), (54, 52), (42, 56)], (90, 160, 230, 255), w=1))
    tool_cursor('textures/AnchorCursor.png', lambda d: (d.line([(46, 38), (46, 56)], fill=(0, 0, 0, 255), width=2), d.arc([38, 46, 54, 58], 0, 180, fill=(0, 0, 0, 255), width=2)))
    tool_cursor('textures/MaterialCursor.png', lambda d: outlined(d, 'rectangle', [38, 40, 54, 56], (150, 120, 90, 255), w=1))

# ============================================================== sky (cube faces)
def value_noise(p, seed=0):
    """Smooth 3D value noise for an (N, 3) array."""
    i = np.floor(p).astype(np.int64); f = p - i; f = f * f * (3 - 2 * f)
    def h(x, y, z):
        n = (x * 73856093) ^ (y * 19349663) ^ (z * 83492791) ^ (seed * 2654435761)
        n = (n ^ (n >> 13)) * 1274126177
        return ((n ^ (n >> 16)) & 0xffff) / 65535.0
    x, y, z = i[:, 0], i[:, 1], i[:, 2]
    fx, fy, fz = f[:, 0], f[:, 1], f[:, 2]
    L = lambda a, b, t: a + (b - a) * t
    return L(L(L(h(x, y, z), h(x + 1, y, z), fx), L(h(x, y + 1, z), h(x + 1, y + 1, z), fx), fy),
             L(L(h(x, y, z + 1), h(x + 1, y, z + 1), fx), L(h(x, y + 1, z + 1), h(x + 1, y + 1, z + 1), fx), fy), fz)

def sky():
    n = 512
    s, t = np.meshgrid((np.arange(n) + 0.5) / n * 2 - 1, (np.arange(n) + 0.5) / n * 2 - 1)
    s, t = s.ravel(), t.ravel(); one = np.ones_like(s)
    # standard cube-map face directions; Lf/Rt/Up/Dn/Bk/Ft fill +X/-X/+Y/-Y/+Z/-Z
    faces = {'lf': (one, -t, -s), 'rt': (-one, -t, s), 'up': (s, one, t), 'dn': (s, -one, -t), 'bk': (s, -t, one), 'ft': (-s, -t, -one)}
    top, horizon, ground = np.array([62, 118, 205]), np.array([196, 218, 240]), np.array([150, 160, 170])
    for k, (x, y, z) in faces.items():
        d = np.stack([x, y, z], 1); d /= np.linalg.norm(d, axis=1, keepdims=True)
        el = d[:, 1:2]
        col = np.where(el > 0, horizon + (top - horizon) * np.clip(el, 0, 1) ** 0.6, horizon + (ground - horizon) * np.clip(-el * 3, 0, 1))
        # clouds on a flat layer above: project the view ray onto it
        up = np.clip(d[:, 1], 0.02, 1)
        q = d[:, [0, 2]] / up[:, None] * 1.6
        pts = np.stack([q[:, 0], q[:, 1], np.zeros_like(up)], 1)
        c = sum(value_noise(pts * f, i) / f for i, f in enumerate((1, 2, 4, 8))) / 1.875
        cover = np.clip((c - 0.5) * 3.2, 0, 1) * np.clip((d[:, 1] - 0.03) * 6, 0, 1)
        shade = 245 - 40 * np.clip((c - 0.6) * 3, 0, 1)
        col = col * (1 - cover[:, None] * 0.85) + shade[:, None] * cover[:, None] * 0.85
        Image.fromarray(np.clip(col, 0, 255).astype(np.uint8).reshape(n, n, 3)).save(path('sky/null_plainsky512_%s.jpg' % k), quality=85)

# ============================================================== sounds (synthesized)
SR = 22050
def env(n, attack=0.005, decay=None):
    t = np.arange(n) / SR; e = np.minimum(1, t / max(attack, 1e-4))
    if decay: e *= np.exp(-t / decay)
    return e
def noise(n): return RNG.uniform(-1, 1, n)
def lowpass(x, k):
    y = np.zeros_like(x); a = 0.0
    for i, v in enumerate(x): a += k * (v - a); y[i] = a
    return y
def tone(freq, n, kind='sine'):
    f = np.broadcast_to(np.asarray(freq, float), (n,)); ph = 2 * np.pi * np.cumsum(f) / SR
    if kind == 'saw': return 2 * ((ph / (2 * np.pi)) % 1) - 1
    if kind == 'square': return np.sign(np.sin(ph))
    return np.sin(ph)
def sec(s): return int(s * SR)
def wav(name, x, gain=0.8):
    x = np.asarray(x, float); m = np.max(np.abs(x)) or 1; x = np.clip(x / m * gain, -1, 1)
    with wave.open(path(name), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype('<i2').tobytes())

def sounds():
    n = sec(0.08); wav('sounds/collide.wav', lowpass(noise(n), 0.25) * env(n, 0.001, 0.02), 0.5)
    n = sec(1.2); wav('sounds/bass.wav', (lowpass(noise(n), 0.05) * 1.5 + tone(np.linspace(70, 35, n), n)) * env(n, 0.003, 0.35))
    n = sec(0.06); wav('sounds/button.wav', tone(1100, n, 'square') * env(n, 0.001, 0.02), 0.4)
    n = sec(0.12); x = np.zeros(n); c = sec(0.012); x[:c] = noise(c) * env(c, 0.0005, 0.003); x[sec(0.06):sec(0.06) + c] = noise(c) * env(c, 0.0005, 0.003)
    wav('sounds/ClickFast.wav', x, 0.5)
    n = sec(0.35); wav('sounds/electronicpingshort.wav', (tone(1760, n) + 0.3 * tone(3520, n)) * env(n, 0.002, 0.08), 0.5)
    n = sec(0.5); wav('sounds/flashbulb.wav', np.concatenate([tone(np.linspace(2000, 6000, sec(0.35)), sec(0.35)) * 0.2, lowpass(noise(sec(0.15)), 0.5) * env(sec(0.15), 0.001, 0.03)]))
    n = sec(1.2); wav('sounds/HalloweenGhost.wav', tone(420 + 60 * np.sin(np.arange(n) / SR * 2 * np.pi * 5) + np.linspace(0, -120, n), n) * np.sin(np.linspace(0, np.pi, n)), 0.5)
    n = sec(0.7); wav('sounds/HalloweenLightning.wav', noise(n) * env(n, 0.001, 0.12) * (1 + 0.8 * np.sign(np.sin(np.arange(n) / SR * 2 * np.pi * 23))))
    n = sec(2.5); wav('sounds/HalloweenThunder.wav', lowpass(noise(n), 0.02) * env(n, 0.15, 0.8) * (1 + 0.5 * np.sin(np.arange(n) / SR * 2 * np.pi * 3)))
    n = sec(0.15); wav('sounds/hit.wav', (lowpass(noise(n), 0.15) + tone(np.linspace(180, 70, n), n)) * env(n, 0.001, 0.04))
    n = sec(0.4); wav('sounds/Kerplunk.wav', tone(np.linspace(900, 180, n) ** 1, n) * env(n, 0.002, 0.12) + lowpass(noise(n), 0.1) * env(n, 0.001, 0.02))
    def whoosh(name, dur, k0, k1, g=0.8, boom=False):
        n = sec(dur); x = noise(n); y = np.zeros(n); a = 0.0; ks = np.linspace(k0, k1, n)
        for i in range(n): a += ks[i] * (x[i] - a); y[i] = a
        y *= np.sin(np.linspace(0, np.pi, n)) ** 0.5
        if boom: y[:sec(0.1)] += lowpass(noise(sec(0.1)), 0.3) * env(sec(0.1), 0.001, 0.03) * 2
        wav(name, y, g)
    whoosh('sounds/Launching rocket.wav', 1.2, 0.05, 0.3, boom=True)
    whoosh('sounds/Rocket shot.wav', 0.6, 0.3, 0.08, boom=True)
    whoosh('sounds/Shoulder fired rocket.wav', 0.9, 0.2, 0.05, boom=True)
    whoosh('sounds/Rocket whoosh 01.wav', 1.5, 0.04, 0.12, 0.6)
    whoosh('sounds/swoosh.wav', 0.35, 0.05, 0.4, 0.5)
    whoosh('sounds/swordslash.wav', 0.3, 0.1, 0.5, 0.6)
    whoosh('sounds/swordlunge.wav', 0.45, 0.4, 0.08, 0.6)
    n = sec(0.12); wav('sounds/paintball.wav', lowpass(noise(n), 0.4) * env(n, 0.001, 0.02) + tone(220, n) * env(n, 0.001, 0.03) * 0.5, 0.5)
    n = sec(0.5); wav('sounds/Rubber band sling shot.wav', tone(np.linspace(240, 150, n), n, 'saw') * env(n, 0.001, 0.1), 0.5)
    n = sec(0.6); wav('sounds/short spring sound.wav', tone(300 + 250 * np.sin(np.linspace(0, 5 * np.pi, n)) * np.exp(-np.arange(n) / SR / 0.25), n) * env(n, 0.002, 0.25), 0.6)
    n = sec(0.3); wav('sounds/splat.wav', lowpass(noise(n), np.linspace(0.6, 0.05, n).mean()) * env(n, 0.001, 0.07), 0.7)
    n = sec(0.6); ring = sum(tone(f, n) * a for f, a in ((2400, 1), (3700, 0.5), (5100, 0.3))) * env(n, 0.003, 0.2)
    wav('sounds/unsheath.wav', ring * 0.6 + lowpass(noise(n), 0.5) * np.linspace(1, 0, n) * 0.4, 0.5)
    # a falling, hollow "oof"-like groan made from a sawtooth and two resonant bands
    n = sec(0.55); f0 = np.linspace(210, 110, n); src = tone(f0, n, 'saw')
    def band(x, fc, q=12):
        w = 2 * np.pi * fc / SR; r = 1 - w / q; y = np.zeros_like(x); y1 = y2 = 0.0
        for i, v in enumerate(x): y0 = v + 2 * r * np.cos(w) * y1 - r * r * y2; y[i] = y0; y2, y1 = y1, y0
        return y
    wav('sounds/uuhhh.wav', (band(src, 520) + 0.6 * band(src, 950)) * env(n, 0.03, 0.3), 0.7)
    notes = (523.25, 659.25, 783.99, 1046.5); parts = []
    for i, f in enumerate(notes):
        n = sec(0.16 if i < 3 else 0.6); parts.append((tone(f, n, 'square') * 0.3 + tone(f, n)) * env(n, 0.004, 0.12 if i < 3 else 0.35))
    wav('sounds/victory.wav', np.concatenate(parts), 0.5)
    # footstep (WAV data; players sniff the format, so the classic .mp3 name still plays)
    n = sec(0.1); wav('sounds/bfsl-minifigfoots1.mp3', lowpass(noise(n), 0.1) * env(n, 0.002, 0.02), 0.5)

# ============================================================== bundle
def bundle():
    files = {}
    for dp, _, fs in os.walk(OUT):
        for f in sorted(fs):
            if f == 'README.txt': continue
            full = os.path.join(dp, f); rel = os.path.relpath(full, OUT).replace(os.sep, '/')
            files[rel] = base64.b64encode(open(full, 'rb').read()).decode()
    src = ('// Generated by tools/make_assets.py from assets/: BrickBuild\'s own stand-in assets, bundled so the\n'
           '// client works with no asset folder. Do not edit by hand.\n'
           'export const BUILTIN_ASSETS: Record<string, string> = ' + json.dumps(files, indent=0, sort_keys=True) + ';\n')
    open(os.path.join(ROOT, 'src/client/builtin-assets.gen.ts'), 'w', newline='\n').write(src)
    return sum(len(v) for v in files.values())

if __name__ == '__main__':
    readme = open(os.path.join(OUT, 'README.txt')).read() if os.path.exists(os.path.join(OUT, 'README.txt')) else None
    shutil.rmtree(OUT, ignore_errors=True); os.makedirs(OUT)
    if readme: open(os.path.join(OUT, 'README.txt'), 'w').write(readme)
    sword(); rocketlauncher(); slingshot(); paintballgun(); trowel(); timebomb()
    icons(); spawn_decal(); cursors(); sky(); sounds()
    shutil.copy(os.path.join(ROOT, 'content/face.png'), path('textures/face.png'))
    print('bundled', bundle() // 1024, 'KB (base64)')
