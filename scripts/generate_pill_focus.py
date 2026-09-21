#!/usr/bin/env python3
"""Build a pillN_focus.png from the existing radius_N / bordertexture-N_alt pair.

A button control cannot carry a <bordertexture>, so the fill and the focus ring
have to live in one texture. pill46_focus.png solves that: its interior is pure
black at alpha A6 and its ring is near-white. Because colordiffuse multiplies,
black x any tint stays black (the A6 fill) while the near-white ring takes the
theme colour. One texture gives a button the same 4D/A6 + border treatment that
list layouts get from two stacked controls.

This regenerates that structure for any radius the skin already has masks for.

    python3 scripts/generate_pill_focus.py 33
"""

import os
import sys

from PIL import Image

MASKS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "media", "masks")

FILL_RGB = (0, 0, 0)
FILL_ALPHA = 166  # 0xA6, matching the A6000000 tiles used everywhere else


def build(radius):
    shape_path = os.path.join(MASKS, "radius_%d.png" % radius)
    ring_path = os.path.join(MASKS, "bordertexture-%d_alt.png" % radius)
    for p in (shape_path, ring_path):
        if not os.path.exists(p):
            raise SystemExit("missing %s" % p)

    shape = Image.open(shape_path).convert("RGBA")
    ring = Image.open(ring_path).convert("RGBA")
    if ring.size != shape.size:
        # the ring defines the 9-slice geometry, so match it
        shape = shape.resize(ring.size, Image.LANCZOS)

    # the rounded-rect silhouette is the shape texture's alpha channel
    alpha = shape.split()[3].point(lambda a: a * FILL_ALPHA // 255)
    fill = Image.new("RGBA", ring.size, FILL_RGB + (0,))
    fill.putalpha(alpha)

    out = Image.alpha_composite(fill, ring)
    out_path = os.path.join(MASKS, "pill%d_focus.png" % radius)
    out.save(out_path, optimize=True)
    return out_path, out


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    for arg in sys.argv[1:]:
        path, im = build(int(arg))
        px = im.load()
        w, h = im.size
        print("%s  %dx%d  centre=%s  edge=%s  %d bytes"
              % (os.path.basename(path), w, h, px[w // 2, h // 2], px[w // 2, 1],
                 os.path.getsize(path)))


if __name__ == "__main__":
    main()
