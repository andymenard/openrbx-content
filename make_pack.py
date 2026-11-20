"""Builds an original content folder for the OpenRBX source port (December 2007 client).

Every file is drawn, synthesized or written here, or comes from BrickBuild (MIT, the same author's
own clean-room engine) via tools/brickbuild_assets.py and tools/brickbuild-tiles/. The one outside
input is the Comic Neue typeface (SIL Open Font License 1.1, vendor/comicneue/), rasterized into
the G3D bitmap font the client draws text with.

    .venv/bin/python make_pack.py          writes content/

File names and formats follow what the client's code asks ContentProvider for; see FILES.md.
"""
import io, math, os, shutil, struct, sys, zlib
import numpy as np
from xml.sax.saxutils import escape
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'content')
TILES = os.path.join(HERE, 'tools', 'brickbuild-tiles')
sys.path.insert(0, os.path.join(HERE, 'tools'))
import brickbuild_assets as bb  # noqa: E402

RNG = np.random.default_rng(2007)

def path(p):
    full = os.path.join(OUT, p)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    return full

# ============================================================== surfaces
# BrickMesh.cpp maps a block face into one greyscale strip, 2 studs wide and 12 studs tall:
#   y 0    .. 1/3   studs   (2 x 4 studs)
#   y 1/3  .. 2/3   inlet   (2 x 4 studs)
#   y 2/3  .. 5/6   weld    (2 x 2 studs)
#   y 5/6  .. 1     glue    (2 x 2 studs)
# Smooth faces sample the single point (strip centre, 8/9), inside the glue band.
# The client tints the strip once per palette colour via TextureProxy::shadePixel: grey 128 is the
# brick colour itself, brighter lightens toward white, darker (< 126) darkens to at most half.
# BrickBuild's tiles are drawn around grey 200, so they are rescaled to put that at 128.
BB_BASE = 200.0

def bb_tile(name, px):
    im = Image.open(os.path.join(TILES, name)).convert('L').resize((px, px), Image.LANCZOS)
    a = np.asarray(im, float) * (128.0 / BB_BASE)
    return a

def surface_strip(stud):
    """stud = pixels per stud. Returns an (12*stud, 2*stud) greyscale array."""
    w = 2 * stud
    studs = np.tile(bb_tile('studs.png', stud), (4, 2))
    inlet = np.tile(bb_tile('inlet.png', stud), (4, 2))
    weld = bb_tile('weld.png', w)
    glue = bb_tile('glue.png', w)
    strip = np.vstack([studs, inlet, weld, glue])
    # the smooth-face sample point and enough around it to survive filtering and mipmaps
    cy, cx = int(round(strip.shape[0] * 8 / 9)), w // 2
    r = max(2, stud // 8)
    strip[cy - r:cy + r + 1, cx - r:cx + r + 1] = 128
    return np.clip(np.rint(strip), 0, 255).astype(np.uint8)

def surfaces():
    Image.fromarray(surface_strip(32), 'L').convert('RGB').save(path('textures/SurfacesStrip.png'))
    # The legacy OGRE renderer builds custom mipmaps for this atlas.
    # A power-of-two height keeps its mip count within the OpenGL limit.
    atlas = Image.fromarray(surface_strip(64)).convert('RGB')
    atlas.resize((128, 1024), Image.Resampling.BILINEAR).save(path('textures/surfaces.png'))

# ============================================================== other textures
def johntex():
    """Default texture for file meshes: near-white so a mesh's VertexColor shows through."""
    n = 128
    a = 235 + RNG.normal(0, 4, (n, n))
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), 'L').convert('RGB').save(path('textures/JohnTex.png'))

def explosion():
    n = 128
    y, x = np.mgrid[0:n, 0:n] + 0.5
    dx, dy = (x - n / 2) / (n / 2), (y - n / 2) / (n / 2)
    r = np.hypot(dx, dy); ang = np.arctan2(dy, dx)
    # a ragged fireball: radius wobbles with angle, hot white core to orange to dark red rim
    edge = 0.78 + 0.12 * np.sin(7 * ang) * np.cos(3 * ang + 1) + 0.05 * np.sin(17 * ang)
    t = np.clip(r / edge, 0, 1.2)
    core = np.array([255, 250, 220]); mid = np.array([255, 160, 40]); rim = np.array([170, 40, 10])
    c = np.where((t < 0.45)[..., None], core + (mid - core) * (t / 0.45)[..., None],
                 mid + (rim - mid) * np.clip((t - 0.45) / 0.55, 0, 1)[..., None])
    alpha = np.clip((1.0 - t) * 6, 0, 1) * 255
    img = np.dstack([np.clip(c, 0, 255), alpha]).astype(np.uint8)
    Image.fromarray(img, 'RGBA').filter(ImageFilter.GaussianBlur(0.8)).save(path('textures/explosion.png'))

# ============================================================== cursors
# Same conventions as BrickBuild's: 64 x 64, the pointer's tip at the centre (32, 32), a small glyph
# to its lower right saying what the tool does.
def cursors():
    K = (0, 0, 0, 255); W = (255, 255, 255, 255)
    def tool_cursor(name, draw):
        im = bb.canvas(); d = ImageDraw.Draw(im); draw(d)
        d.polygon([(32, 32), (32, 42), (35, 39), (40, 40)], fill=W, outline=K); bb.save(im, name)
    o = bb.outlined
    def brick(d, fill, top=None):
        o(d, 'rectangle', [38, 44, 56, 54], fill, w=1)
        if top: top(d)
    def studs(d):
        brick(d, (200, 200, 200, 255))
        for x in (42, 50): o(d, 'rectangle', [x, 40, x + 4, 44], (220, 220, 220, 255), w=1)
    def inlet(d):
        brick(d, (200, 200, 200, 255))
        for x in (42, 50): d.ellipse([x, 46, x + 4, 50], fill=(90, 90, 90, 255))
    def flat(d): brick(d, (200, 200, 200, 255))
    def weld(d):
        brick(d, (200, 200, 200, 255)); d.line([(38, 49), (56, 49)], fill=(220, 120, 20, 255), width=3)
    def glue(d):
        brick(d, (200, 200, 200, 255))
        for x in (41, 47, 53): d.ellipse([x - 2, 47, x + 2, 51], fill=(80, 200, 80, 255))
    def hinge(d):
        brick(d, (200, 200, 200, 255)); o(d, 'ellipse', [42, 44, 52, 54], (240, 220, 40, 255), w=1)
    def motor(d):
        brick(d, (200, 200, 200, 255)); o(d, 'ellipse', [42, 44, 52, 54], (240, 220, 40, 255), w=1)
        d.arc([40, 42, 54, 56], 200, 340, fill=K, width=2)
    def padlock(d, shut):
        o(d, 'rounded_rectangle', [40, 46, 54, 57], (230, 190, 50, 255), w=1, radius=2)
        if shut: d.arc([42, 38, 52, 50], 180, 360, fill=K, width=2)
        else: d.arc([46, 36, 56, 48], 180, 360, fill=K, width=2)
    def anchor(d, cross):
        d.line([(46, 38), (46, 56)], fill=K, width=2); d.arc([38, 46, 54, 58], 0, 180, fill=K, width=2)
        d.line([(42, 41), (50, 41)], fill=K, width=2)
        if cross: d.line([(38, 38), (56, 58)], fill=(220, 30, 30, 255), width=3)
    def clone(d, over):
        o(d, 'rectangle', [38, 44, 48, 54], (90, 160, 230, 255), w=1)
        o(d, 'rectangle', [44, 40, 54, 50], (140, 200, 250, 255) if not over else (255, 230, 120, 255), w=1)
    def hammer(d, over):
        head = (130, 135, 145, 255) if not over else (230, 80, 60, 255)
        o(d, 'rectangle', [38, 40, 54, 46], head, w=1); d.line([(46, 46), (46, 58)], fill=(150, 100, 55, 255), width=3)
    def direction(d):
        d.line([(38, 50), (56, 50)], fill=K, width=2)
        d.polygon([(56, 50), (50, 45), (50, 55)], fill=(220, 60, 60, 255), outline=K)
    def dropper(d):
        d.line([(40, 56), (50, 46)], fill=K, width=3)
        o(d, 'ellipse', [48, 38, 56, 46], (90, 160, 230, 255), w=1)
    def resize(d):
        for a, b in (((38, 49), (56, 49)), ((47, 40), (47, 58))): d.line([a, b], fill=K, width=2)
        for tip, l, r in (((38, 49), (42, 46), (42, 52)), ((56, 49), (52, 46), (52, 52)),
                          ((47, 40), (44, 44), (50, 44)), ((47, 58), (44, 54), (50, 54))):
            d.polygon([tip, l, r], fill=(90, 190, 90, 255), outline=K)
    for name, fn in (('Studs', studs), ('Inlet', inlet), ('Flat', flat), ('Weld', weld), ('Glue', glue),
                     ('Hinge', hinge), ('Motor', motor), ('Lock', lambda d: padlock(d, True)),
                     ('Unlock', lambda d: padlock(d, False)), ('UnAnchor', lambda d: anchor(d, True)),
                     ('Clone', lambda d: clone(d, False)), ('CloneOver', lambda d: clone(d, True)),
                     ('HammerOver', lambda d: hammer(d, True)), ('Direction', direction),
                     ('Dropper', dropper), ('Resize', resize)):
        tool_cursor('textures/%sCursor.png' % name, fn)

# ============================================================== sounds
def sounds():
    S, sec, env, noise, lowpass, tone, wav = bb.SR, bb.sec, bb.env, bb.noise, bb.lowpass, bb.tone, bb.wav
    # glass: a crack, then a shower of short bright tinkles
    n = sec(1.0); x = lowpass(noise(n), 0.7) * env(n, 0.0005, 0.03) * 1.5
    for _ in range(40):
        at = int(RNG.uniform(0.01, 0.75) * S); m = sec(RNG.uniform(0.04, 0.12)); f = RNG.uniform(2500, 7000)
        if at + m < n: x[at:at + m] += tone(f, m) * env(m, 0.0005, 0.02) * RNG.uniform(0.2, 0.6)
    wav('sounds/glassbreak.wav', x, 0.7)
    # switches: a two-part mechanical click, and a lower, heavier toggle
    def click(m, k, decay): return lowpass(noise(m), k) * env(m, 0.0003, decay)
    n = sec(0.08); x = np.zeros(n); a = click(sec(0.01), 0.6, 0.002); x[:a.size] += a; x[sec(0.035):sec(0.035) + a.size] += 0.6 * a
    wav('sounds/switch.wav', x, 0.5)
    n = sec(0.14); x = np.zeros(n); a = click(sec(0.02), 0.25, 0.005); b = tone(np.linspace(260, 140, sec(0.05)), sec(0.05)) * env(sec(0.05), 0.001, 0.015)
    x[:a.size] += a; x[sec(0.06):sec(0.06) + b.size] += b
    wav('sounds/SWITCH3.wav', x, 0.5)
    # page turn: a soft papery swish that rises and falls
    n = sec(0.4); k = np.linspace(0.08, 0.35, n); y = np.zeros(n); acc = 0.0; src = noise(n)
    for i in range(n): acc += k[i] * (src[i] - acc); y[i] = acc
    y *= np.sin(np.linspace(0, np.pi, n)) ** 1.5
    wav('sounds/pageturn.wav', y, 0.4)
    # snap: a sharp tick over a short low knock, for joints clicking together
    n = sec(0.1); x = click(n, 0.9, 0.003) + tone(np.linspace(420, 180, n), n) * env(n, 0.0005, 0.012) * 0.7
    wav('sounds/snap.wav', x, 0.6)

# ============================================================== bitmap font (G3D GFont v1)
# GFont.cpp: zlib file = uint32 LE uncompressed length + compress2 stream of
#   int32 version (1), uint16 subWidth[128], uint16 baseline, uint16 texWidth,
#   A8 texels, 16 x 8 cells of texWidth/16 each (texWidth x texWidth/2, powers of two).
# A glyph is drawn centred in its cell; subWidth is its advance in texels.
def g3d_font(ttf, out, cell=32, size=26):
    font = ImageFont.truetype(ttf, size)
    tex = Image.new('L', (cell * 16, cell * 8), 0); d = ImageDraw.Draw(tex)
    asc, desc = font.getmetrics()
    top = (cell - (asc + desc)) // 2
    baseline = top + asc
    widths = []
    for c in range(128):
        ch = chr(c)
        if c < 32 or c == 127:
            widths.append(0); continue
        adv = int(round(font.getlength(ch)))
        widths.append(min(cell, adv + 1))
        if ch == ' ': continue
        col, row = c % 16, c // 16
        x = col * cell + (cell - adv) / 2
        d.text((x, row * cell + top), ch, font=font, fill=255)
    body = struct.pack('<i', 1) + struct.pack('<128H', *widths) + struct.pack('<HH', baseline, cell * 16) + tex.tobytes()
    with open(path(out), 'wb') as f:
        f.write(struct.pack('<I', len(body)) + zlib.compress(body, 9))
    tex.save(os.path.join(HERE, 'build', os.path.basename(out) + '.preview.png'))

def fonts():
    os.makedirs(os.path.join(HERE, 'build'), exist_ok=True)
    g3d_font(os.path.join(HERE, 'vendor/comicneue/ComicNeue-Bold.ttf'), 'fonts/comics.fnt')
    shutil.copy(os.path.join(HERE, 'vendor/comicneue/OFL.txt'), path('fonts/comics-OFL.txt'))

# ============================================================== data files
def wordlist():
    # ProfanityFilter.cpp reads Fonts\diogenes.fnt as plain text, one blocked word per line,
    # lowercased and trimmed. Shipped empty: the list is policy for whoever runs a server.
    open(path('fonts/diogenes.fnt'), 'w', newline='\n').close()

SAFECHAT = [
    ('Hello', ['Hi!', 'Hello!', 'Hey there!', 'Good morning!', 'Good evening!', 'Welcome!']),
    ('Goodbye', ['Bye!', 'See you later!', 'I have to go now.', 'Thanks for playing!']),
    ('Building', ['Want to build together?', 'Nice build!', 'Can I help?', 'What are you making?',
                  'I am building a house.', 'I am building a car.', 'Let\'s make a tower!']),
    ('Games', ['Let\'s play a game!', 'Tag, you\'re it!', 'Race you!', 'Hide and seek?', 'Follow me!', 'Good game!']),
    ('Questions', ['How do I do that?', 'Where are you?', 'What should we do?', 'Can you help me?', 'Who wants to team up?']),
    ('Answers', ['Yes', 'No', 'Maybe', 'OK', 'I don\'t know', 'Sure!', 'One moment, please.']),
    ('Feelings', ['Cool!', 'Awesome!', 'Oops!', 'Sorry!', 'Thank you!', 'That was fun!', 'Wow!']),
]

def safechat():
    # SafeChat.cpp: any root element; each <utterance> holds its text, and may nest more <utterance>s.
    def esc(s): return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    lines = ['<?xml version="1.0" encoding="utf-8"?>', '<safechat>']
    for head, items in SAFECHAT:
        lines.append('\t<utterance>%s' % esc(head))
        for it in items: lines.append('\t\t<utterance>%s</utterance>' % esc(it))
        lines.append('\t</utterance>')
    lines.append('</safechat>')
    open(path('fonts/safechat.xml'), 'w', newline='\n').write('\n'.join(lines) + '\n')

# ============================================================== models (XML, <roblox version="4">)
# SerializerV2/XmlSerializer: <Item class referent><Properties> with typed children named by the
# property's XML name (Part: CFrame, size, shape, formFactor, BrickColor as <int>, surfaces as
# <token>). Enum values: shape Ball 0 / Block 1 / Cylinder 2; formFactor Symmetric 0;
# surfaces Smooth 0, Studs 3, Inlet 4; face Front = 5 (-Z).
class Rbxm:
    def __init__(self): self.n = 0
    def item(self, cls, props, children=()):
        ref = 'RBX%d' % self.n; self.n += 1
        out = ['<Item class="%s" referent="%s">' % (cls, ref), '<Properties>']
        for kind, name, val in props:
            if kind == 'CoordinateFrame':
                x, y, z = val
                out.append('<CoordinateFrame name="%s"><X>%g</X><Y>%g</Y><Z>%g</Z>'
                           '<R00>1</R00><R01>0</R01><R02>0</R02><R10>0</R10><R11>1</R11><R12>0</R12>'
                           '<R20>0</R20><R21>0</R21><R22>1</R22></CoordinateFrame>' % (name, x, y, z))
            elif kind == 'Vector3':
                out.append('<Vector3 name="%s"><X>%g</X><Y>%g</Y><Z>%g</Z></Vector3>' % ((name,) + tuple(val)))
            elif kind == 'Content':
                out.append('<Content name="%s"><url>%s</url></Content>' % (name, val))
            elif kind == 'bool':
                out.append('<bool name="%s">%s</bool>' % (name, 'true' if val else 'false'))
            elif kind == 'string':
                out.append('<string name="%s">%s</string>' % (name, escape(val)))
            else:
                out.append('<%s name="%s">%s</%s>' % (kind, name, val, kind))
        out.append('</Properties>')
        out.extend(children)
        out.append('</Item>')
        return '\n'.join(out)
    @staticmethod
    def file(name, items):
        body = '<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" version="4">\n%s\n</roblox>\n' % '\n'.join(items)
        open(path(name), 'w', newline='\n').write(body)

def part(r, name, size, at, color, shape=1, top=0, bottom=0, extra=(), children=()):
    return r.item('Part', [('string', 'Name', name), ('CoordinateFrame', 'CFrame', at), ('Vector3', 'size', size),
                           ('int', 'BrickColor', color), ('token', 'shape', shape), ('token', 'formFactor', 0),
                           ('token', 'TopSurface', top), ('token', 'BottomSurface', bottom)] + list(extra), children)

def models():
    # ToolsSurface.cpp: each file's first item is the projectile Part the tool fires
    r = Rbxm(); Rbxm.file('fonts/SlingshotPellet.rbxm', [part(r, 'Pellet', (1, 1, 1), (0, 0, 0), 199, shape=0)])
    r = Rbxm(); Rbxm.file('fonts/Rocket.rbxm', [part(r, 'Rocket', (1, 1, 4), (0, 0, 0), 194)])
    # Player.cpp: exactly one Model holding a Humanoid; Humanoid::buildJoints joins parts named
    # Head, Torso, Left/Right Arm, Left/Right Leg with offsets that fix a 2x2x1 torso, 1x2x1 limbs
    # and a head on top. Colours are this pack's own (2007 palette): light reddish violet head and
    # arms, brown shirt, dark stone grey trousers.
    r = Rbxm(); SKIN, SHIRT, PANTS = 9, 217, 199
    face = r.item('Decal', [('string', 'Name', 'face'), ('token', 'Face', 5),
                            ('Content', 'Texture', 'rbxasset://textures/character-face.png')])
    head_mesh = r.item('SpecialMesh', [
        ('string', 'Name', 'Mesh'), ('token', 'MeshType', 0), ('Vector3', 'Scale', (1.22, 1.22, 1.22)),
    ])
    body = [
        part(r, 'Head', (2, 1, 1), (0, 4.5, 0), SKIN, children=[head_mesh, face]),
        part(r, 'Torso', (2, 2, 1), (0, 3, 0), SHIRT, top=3, bottom=4),
        part(r, 'Left Arm', (1, 2, 1), (-1.5, 3, 0), SKIN, top=3, bottom=4),
        part(r, 'Right Arm', (1, 2, 1), (1.5, 3, 0), SKIN, top=3, bottom=4),
        part(r, 'Left Leg', (1, 2, 1), (-0.5, 1, 0), PANTS, top=3, bottom=4),
        part(r, 'Right Leg', (1, 2, 1), (0.5, 1, 0), PANTS, top=3, bottom=4),
        r.item('Humanoid', [('string', 'Name', 'Humanoid')]),
    ]
    Rbxm.file('fonts/character.rbxm', [r.item('Model', [('string', 'Name', 'Character')], body)])
    # Player.cpp parents these items to the model before it enters Workspace.
    with open(os.path.join(HERE, 'tools', 'animate.lua'), encoding='utf-8') as source:
        animation = source.read()
    r = Rbxm()
    Rbxm.file('fonts/humanoidAnimate.rbxm', [r.item('Script', [
        ('string', 'Name', 'Animate'), ('string', 'Source', animation),
    ])])
    for n in ('humanoidSound', 'humanoidHealth'):
        Rbxm.file('fonts/%s.rbxm' % n, [])

def character_face():
    # Keep the features away from the cap bevels, where the head mesh warps the UVs.
    oversample = 4
    face = Image.new('RGBA', (256 * oversample, 256 * oversample))
    draw = ImageDraw.Draw(face)
    ink = (37, 25, 29, 255)

    for center in (96, 160):
        draw.ellipse(tuple(value * oversample for value in (center - 7, 89, center + 7, 108)), fill=ink)

    draw.arc(tuple(value * oversample for value in (90, 104, 166, 151)),
             start=15, end=165, fill=ink, width=6 * oversample)
    face.resize((256, 256), Image.Resampling.LANCZOS).save(path('textures/character-face.png'))


def celestial_textures():
    # OGRE adds these billboards to the sky, so black contributes no light.
    coords = (np.arange(256) + 0.5) / 128 - 1
    x, y = np.meshgrid(coords, coords)
    radius = np.hypot(x, y)

    def save(name, rgb):
        pixels = np.clip(rgb, 0, 255).astype(np.uint8)
        Image.fromarray(pixels).save(path(f'sky/{name}.jpg'), quality=95)

    moon_radius = radius / 0.77
    sphere = np.sqrt(np.maximum(0, 1 - moon_radius ** 2))
    shading = np.clip(0.4 + 0.65 * sphere - 0.28 * x, 0, 1)
    for cx, cy, size in [(-0.25, -0.17, 0.12), (0.20, 0.13, 0.17),
                         (-0.10, 0.39, 0.08), (0.30, -0.32, 0.07)]:
        shading *= 1 - 0.27 * np.exp(-((x - cx) ** 2 + (y - cy) ** 2) / size ** 2)
    moon = shading * np.clip((1 - moon_radius) * 90, 0, 1)
    save('moon', moon[..., None] * np.array([216, 225, 240]))

    fade = np.clip((0.97 - radius) * 8, 0, 1)
    disc = np.clip((0.22 - radius) * 90, 0, 1)
    sun = np.maximum(disc, 0.32 * np.exp(-8 * radius)) * fade
    save('sun', sun[..., None] * np.array([255, 243, 204]))

    angle = np.arctan2(y, x)
    beams = (0.5 + 0.5 * np.cos(12 * angle)) ** 5
    rays = beams * np.exp(-3 * radius) * np.minimum(radius * 8, 1) * fade
    save('sun-rays', rays[..., None] * np.array([255, 221, 153]))


# ============================================================== from BrickBuild as is
def from_brickbuild():
    bb.OUT = OUT; bb.ROOT = os.path.join(HERE, 'tools', 'no-brickbuild-ui')  # small icons fall back to drawn ones
    bb.sword(); bb.rocketlauncher(); bb.slingshot(); bb.paintballgun(); bb.trowel(); bb.timebomb()
    bb.icons(); bb.spawn_decal(); bb.cursors(); bb.sky(); bb.sounds()
    shutil.copy(os.path.join(TILES, 'face.png'), path('textures/face.png'))
    # Sound.cpp asks for "clickfast"; keep BrickBuild's spelling too
    shutil.copy(path('sounds/ClickFast.wav'), path('sounds/clickfast.tmp'))
    os.remove(path('sounds/ClickFast.wav')); os.rename(path('sounds/clickfast.tmp'), path('sounds/clickfast.wav'))

if __name__ == '__main__':
    shutil.rmtree(OUT, ignore_errors=True); os.makedirs(OUT)
    from_brickbuild()
    celestial_textures()
    character_face()
    surfaces(); johntex(); explosion(); cursors(); sounds(); fonts(); wordlist(); safechat(); models()
    n = sum(len(fs) for _, _, fs in os.walk(OUT))
    print('wrote', n, 'files to', OUT)
