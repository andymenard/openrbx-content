# What the client asks for

From the OpenRBX source at `OpenRBX-org/OpenRBX` (paths under `Client/`). Status: **ok** = shipped
and in the format the code reads; **stub** = shipped, but minimal; **todo** = not yet.

| File | Asked for in | Status | Notes |
|---|---|---|---|
| `sky/null_plainsky512_{bk,dn,ft,lf,rt,up}.jpg` | `App/v8datamodel/Sky.cpp:91`, `Rendering/RenderLibNew/View.cpp:135` | ok | 512² cube faces, procedural sky and clouds |
| `sky/{moon,sun,sun-rays}.jpg` | `Rendering/AppDraw/RbxSky.cpp` | ok | 256² procedural textures for additive billboards |
| `textures/SurfacesStrip.png` | `RbxView/MaterialFactory.cpp:138` | ok | greyscale, 64×384: studs / inlet / weld / glue bands at 0, ⅓, ⅔, ⅚ (`BrickMesh.cpp:96`). Grey 128 = brick colour (`TextureProxy::shadePixel`). Smooth faces sample (centre, 8/9), kept at 128 |
| `textures/surfaces.png` | `RbxView/MaterialFactory.cpp:132` | ok | same normalized layout at 128×1024 for the legacy OpenGL mipmap path |
| `textures/JohnTex.png` | `RbxView/MaterialFactory.cpp:135` | ok | near-white, so a file mesh's vertex colour shows |
| `textures/explosion.png` | `Rendering/AppDraw/AdornRbxGfx.cpp:786` | ok | RGBA fireball |
| `textures/<Name>Cursor.png` ×25 | `App/v8datamodel/MouseCommand.cpp:74` (`getCursorName()`) | ok | 64², tip at centre |
| `textures/{Grab,Clone,Hammer,GameTool}.png` | `App/v8datamodel/Hopper.cpp:249` (HopperBin legacy texture) | ok | |
| `sounds/*.wav` ×14 | `App/util/Sound.cpp:1117` | ok | 22 kHz mono PCM, synthesized |
| `fonts/comics.fnt` | `Rendering/AppDraw/Fonts.cpp:13`, `AdornRbxGfx.cpp:660` | ok | G3D GFont v1 (zlib), 512×256 A8, from Comic Neue Bold |
| `fonts/diogenes.fnt` | `App/gui/ProfanityFilter.cpp:24` | stub | not a font: plain-text word list, one per line. Shipped empty |
| `fonts/safechat.xml` | `App/v8datamodel/SafeChat.cpp:30` | ok | original phrase tree, nested `<utterance>` |
| `fonts/SlingshotPellet.rbxm`, `fonts/Rocket.rbxm` | `App/tool/ToolsSurface.cpp:388` | ok | one Part each |
| `fonts/character.rbxm` | `Network/Player.cpp:342` | ok | one Model with a Humanoid, limbs, and a rounded Head SpecialMesh with a face decal |
| `fonts/humanoidAnimate.rbxm` | `Network/Player.cpp` | ok | drives the four limb motors for locomotion and airborne poses |
| `fonts/humanoid{Sound,Health}.rbxm` | `Network/Player.cpp` | stub | empty models |
| `fonts/LDraw2RobloxMap.xml` | `win/LDrawParser.cpp:24` | todo | only for LDraw import |
| `spot_shadow_fade.png` | `Rendering/AppDraw/RbxSceneManager.cpp:1762` | n/a | OGRE has it built in |

Extra files places of the period refer to (tool meshes and textures, backpack icons, seasonal
icons, the spawn decal, the face) come from BrickBuild as-is.

## What has been checked in the client

The checked-in pack was tested with the OpenRBX ARM64 Linux client and the
OGRE OpenGL renderer on an Apple M1 Pro. A local place rendered with studded
surfaces, the player model, HUD text, and the cursor. The renderer loaded the
512×256 font atlas, all six skybox faces, and the three celestial textures.
The rounded head and limb movement were checked during local play.

An earlier Windows NMake test opened a place and loaded the font atlas before
the VM's Direct3D device was lost. The current pack's full 3D rendering was
verified on Linux.
