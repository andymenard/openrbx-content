# OpenRBX free content

An original replacement for the client's `content` folder, for the
[OpenRBX](https://github.com/OpenRBX-org/OpenRBX) source port (see its issue #2). Nothing in it
comes from Roblox: every file is drawn, synthesized or written by `make_pack.py`, or comes from
[BrickBuild](BRICKBUILD-LICENSE.txt) (MIT), except the Comic Neue typeface (SIL OFL 1.1).

## Install the content pack

Download this repository and copy its ready-to-use `content/` folder beside
your OpenRBX executable (`Roblox` on Linux or `Roblox.exe` on Windows). If that
directory already has a `content/` folder, back it up and copy this pack in
its place. No Python setup is required.

In `AppSettings.xml` beside the executable, set `ContentFolder` inside the
existing `Settings` element. Create the file with the following contents if it
doesn't exist.

```xml
<Settings>
  <ContentFolder>content</ContentFolder>
</Settings>
```

Launch OpenRBX and open a local `.rbxl` place.

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
