# What the client asks for

From the OpenRBX source at `OpenRBX-org/OpenRBX` (paths under `Client/`). Status: **ok** = shipped
and in the format the code reads; **stub** = shipped, but minimal; **todo** = not yet.

| File | Asked for in | Status | Notes |
|---|---|---|---|
| `sky/null_plainsky512_{bk,dn,ft,lf,rt,up}.jpg` | `App/v8datamodel/Sky.cpp:91`, `Rendering/RenderLibNew/View.cpp:135` | ok | 512² cube faces, procedural sky and clouds |
| `textures/SurfacesStrip.png` | `RbxView/MaterialFactory.cpp:138` | ok | greyscale, 64×384: studs / inlet / weld / glue bands at 0, ⅓, ⅔, ⅚ (`BrickMesh.cpp:96`). Grey 128 = brick colour (`TextureProxy::shadePixel`). Smooth faces sample (centre, 8/9), kept at 128 |
| `textures/surfaces.png` | `RbxView/MaterialFactory.cpp:132` | ok? | same layout at 128×768. Used for non-block parts; layout assumed to match the strip, unverified |
| `textures/JohnTex.png` | `RbxView/MaterialFactory.cpp:135` | ok | near-white, so a file mesh's vertex colour shows |
| `textures/explosion.png` | `Rendering/AppDraw/AdornRbxGfx.cpp:786` | ok | RGBA fireball |
| `textures/<Name>Cursor.png` ×25 | `App/v8datamodel/MouseCommand.cpp:74` (`getCursorName()`) | ok | 64², tip at centre |
| `textures/{Grab,Clone,Hammer,GameTool}.png` | `App/v8datamodel/Hopper.cpp:249` (HopperBin legacy texture) | ok | |
| `sounds/*.wav` ×14 | `App/util/Sound.cpp:1117` | ok | 22 kHz mono PCM, synthesized |
| `fonts/comics.fnt` | `Rendering/AppDraw/Fonts.cpp:13`, `AdornRbxGfx.cpp:660` | ok | G3D GFont v1 (zlib), 512×256 A8, from Comic Neue Bold |
| `fonts/diogenes.fnt` | `App/gui/ProfanityFilter.cpp:24` | stub | not a font: plain-text word list, one per line. Shipped empty |
| `fonts/safechat.xml` | `App/v8datamodel/SafeChat.cpp:30` | ok | original phrase tree, nested `<utterance>` |
| `fonts/SlingshotPellet.rbxm`, `fonts/Rocket.rbxm` | `App/tool/ToolsSurface.cpp:388` | ok | one Part each |
| `fonts/character.rbxm` | `Network/Player.cpp:342` | ok | one Model: Humanoid + Head/Torso/arms/legs; this pack's own colours |
| `fonts/humanoid{Sound,Health,Animate}.rbxm` | `Network/Player.cpp:360` | stub | empty models: no scripts yet |
| `fonts/LDraw2RobloxMap.xml` | `win/LDrawParser.cpp:24` | todo | only for LDraw import |
| `spot_shadow_fade.png` | `Rendering/AppDraw/RbxSceneManager.cpp:1762` | n/a | OGRE has it built in |

Extra files places of the period refer to (tool meshes and textures, backpack icons, seasonal
icons, the spawn decal, the face) come from BrickBuild as-is.

## What has been checked in the client

Run with the port's own `Roblox.exe` (NMake build), `AppSettings.xml` pointing at this folder, and
the renderer DLLs from an original December 2007 install (`rgmain.dll`, `rgdx.dll`,
`SciLexer.dll`; none of the original `content` folder):

- the client takes the folder (`setAssetFolder ...\content` in its log) and opens a place;
- `fonts/comics.fnt` is accepted: OGRE logs `ft0` as a 512x256 A8 texture.

Not seen on screen yet. The test machine is a VM whose only Direct3D device is the Microsoft Basic
Render Driver: the device is lost right after the font loads and the client exits. The install
also lacks `rgpar.dll` (OGRE's ParticleFX plugin, renamed), which `VisualEngine.cpp` treats as
fatal; the run above used a local build with that check relaxed. A machine with a real GPU and
a complete install is needed to look at the surfaces, sky and cursors.
