#!/usr/bin/env python3
"""Generate a 9-slice border texture for a given corner radius.

The skin's border textures follow one spec (see the texture-optimization notes):

    size    (radius * 2) + 2, square
    stroke  drawn inside the edge
    colour  RGB 217,217,217 at full alpha, tinted at render time by colordiffuse

and three stroke weights, distinguished by suffix:

    bordertexture-<N>.png        6px   base
    bordertexture-<N>_alt.png    4px   the thin variant used by converted surfaces
    bordertexture-<N>-thin.png   2px

Drawn supersampled and downsampled with BOX (area average), which is what the
original exports look like: the curved corners antialias, but the straight edges
stay hard at full alpha. LANCZOS is wrong here -- its ringing softens the straight
edges to ~238/17 instead of 255/0, and the border renders visibly dimmer.

Usage:
    generate_border_texture.py <radius> [stroke] [suffix]

Examples:
    generate_border_texture.py 15 4 _alt     -> bordertexture-15_alt.png, 32x32, 4px
    generate_border_texture.py 30 6          -> bordertexture-30.png,     62x62, 6px
"""

import os
import sys

from PIL import Image, ImageDraw

SS = 8
RGB = (217, 217, 217)
MASK_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "media", "masks")


def generate(radius, stroke=6, suffix=""):
    size = radius * 2 + 2

    big = Image.new("RGBA", (size * SS, size * SS), (255, 255, 255, 0))
    ImageDraw.Draw(big).rounded_rectangle(
        (0, 0, size * SS - 1, size * SS - 1),
        radius=radius * SS,
        outline=RGB + (255,),
        width=stroke * SS,
    )
    out = big.resize((size, size), Image.BOX)

    path = os.path.join(MASK_DIR, "bordertexture-%d%s.png" % (radius, suffix))
    out.save(path, optimize=True)
    return path, size


def main():
    if len(sys.argv) < 2 or len(sys.argv) > 4:
        print(__doc__.strip())
        return 1

    radius = int(sys.argv[1])
    stroke = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    suffix = sys.argv[3] if len(sys.argv) > 3 else ""

    path, size = generate(radius, stroke, suffix)
    print("%s  %dx%d  radius %d  stroke %dpx" % (path, size, size, radius, stroke))
    return 0


if __name__ == "__main__":
    sys.exit(main())
