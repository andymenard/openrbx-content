# OpenRBX free content

An original replacement for the client's `content` folder, for the
[OpenRBX](https://github.com/OpenRBX-org/OpenRBX) source port (see its issue #2). Nothing in it
comes from Roblox: every file is drawn, synthesized or written by `make_pack.py`, or comes from
[BrickBuild](BRICKBUILD-LICENSE.txt) (MIT), except the Comic Neue typeface (SIL OFL 1.1).

## Install the content pack

1. Build OpenRBX, then open the output directory that contains `Roblox` on
   Linux or `Roblox.exe` on Windows.
2. [Download the content pack](https://github.com/andymenard/openrbx-content/archive/refs/heads/main.zip)
   and extract it. Back up any existing `content/` folder in the build output,
   then copy the extracted `content/` folder beside the executable.
3. Open `AppSettings.xml` beside the executable. Set `ContentFolder` inside
   the existing `Settings` element and keep any other settings. If the file
   doesn't exist, create it with these contents.

   ```xml
   <Settings>
     <ContentFolder>content</ContentFolder>
   </Settings>
   ```

4. Launch OpenRBX, open a local `.rbxl` place, and start a play session to try
   WASD movement and Space to jump.

The ready-to-use files are checked into `content/`. You can install them after
building OpenRBX, without running Python or rebuilding the client.

The pack was tested on ARM64 Linux with OpenGL. The test covered keyboard
movement, jumping, walking animation, and rendering the character, cursors,
HUD font, brick surfaces, and sky. The test build had audio disabled. See
[FILES.md](FILES.md) for asset coverage and Windows test details.

## Regenerate the pack

From the repository root, install NumPy and Pillow in your Python environment
with `python -m pip install numpy pillow`. Run `python make_pack.py` to rebuild
`content/`, or `python tools/preview.py` to generate `build/preview.png`.

[FILES.md](FILES.md) lists every file the client asks for, where in the code it asks, and what
this pack ships for it.

## Licences

- `make_pack.py`, `tools/`, and the generated files: MIT (see [LICENSE](LICENSE)).
  `tools/brickbuild_assets.py` and `tools/brickbuild-tiles/` are BrickBuild's own, also MIT
  ([BRICKBUILD-LICENSE.txt](BRICKBUILD-LICENSE.txt)).
- `content/fonts/comics.fnt` is rasterized from Comic Neue Bold, © 2014 The Comic Neue Project
  Authors, under the SIL Open Font License 1.1 (`vendor/comicneue/OFL.txt`, shipped next to the
  font as `comics-OFL.txt`).

MIT and OFL are both compatible with OpenRBX's GPLv3.
