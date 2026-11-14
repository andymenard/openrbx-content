"""A small original place for eyeballing the pack: every surface, several colours, shapes, a file mesh."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import make_pack as mp
mp.OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'build')
r = mp.Rbxm(); items = []
items.append(mp.part(r, 'Baseplate', (64, 1.2, 64), (0, 0.6, 0), 194, top=3, extra=[('bool', 'Anchored', True), ('bool', 'Locked', True)]))
colors = [21, 23, 24, 37, 1, 26, 105, 192]
for i, c in enumerate(colors):
    items.append(mp.part(r, 'Brick%d' % c, (4, 1.2, 2), (-14 + i * 4, 1.8 + 0, -6), c, top=3, bottom=4, extra=[('bool', 'Anchored', True)]))
for i, (name, top) in enumerate((('Smooth', 0), ('Glue', 1), ('Weld', 2), ('Studs', 3), ('Inlet', 4))):
    items.append(mp.part(r, name, (4, 4, 4), (-12 + i * 6, 3.2, 4), 23 if i % 2 else 21, top=top, bottom=4,
                         extra=[('bool', 'Anchored', True), ('token', 'FrontSurface', top), ('token', 'RightSurface', top)]))
items.append(mp.part(r, 'Ball', (4, 4, 4), (10, 3.2, -14), 24, shape=0, extra=[('bool', 'Anchored', True)]))
items.append(mp.part(r, 'Cylinder', (4, 4, 4), (16, 3.2, -14), 37, shape=2, extra=[('bool', 'Anchored', True)]))
mesh = r.item('SpecialMesh', [('token', 'MeshType', 5), ('Content', 'MeshId', 'rbxasset://fonts/sword.mesh'),
                              ('Content', 'TextureId', 'rbxasset://textures/SwordTexture.png'), ('Vector3', 'Scale', (2, 2, 2))])
items.append(mp.part(r, 'Sword', (1, 1, 4), (0, 4, -14), 194, extra=[('bool', 'Anchored', True)], children=[mesh]))
ws = r.item('Workspace', [('string', 'Name', 'Workspace')], items)
mp.Rbxm.file('test.rbxl', [ws])
print('build/test.rbxl')
