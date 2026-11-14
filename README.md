# OpenRBX free content

An original replacement for the client's `content` folder, for the
[OpenRBX](https://github.com/OpenRBX-org/OpenRBX) source port (see its issue #2). Nothing in it
comes from Roblox: every file is drawn, synthesized or written by `make_pack.py`, or comes from
[BrickBuild](BRICKBUILD-LICENSE.txt) (MIT), except the Comic Neue typeface (SIL OFL 1.1).

```sh
python3 -m venv .venv && .venv/bin/pip install numpy pillow
.venv/bin/python make_pack.py        # writes content/
.venv/bin/python tools/preview.py    # build/preview.png: tinted surfaces, cursors, font
```

To use it, put `content/` next to `Roblox.exe` and point `AppSettings.xml` at it:

```xml
<Settings>
  <ContentFolder>content</ContentFolder>
</Settings>
```

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
