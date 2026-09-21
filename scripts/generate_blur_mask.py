#!/usr/bin/env python3
"""Generate a blur diffuse mask for a dialog panel.

DialogBackgroundCommons paints the blurred background as:

    <texture diffuse="$PARAM[blur_mask]" ...>$VAR[DialogBackgroundTexture]</texture>

so the mask supplies the panel's alpha shape. Masks are stored at quarter
of the panel's on-screen size -- the GPU scales them back up at render
time and the blur is soft enough that nothing is lost. See the
"Altus blur textures are quarter-size" note: this is load-bearing for
memory, never raise the source resolution.

The mask is drawn at full size and downsampled, which antialiases the
corners the same way the Figma exports did.

Usage:
    generate_blur_mask.py <name> <panel_width> <panel_height> [radius]

Panel width/height are the dimensions of the background image control --
that is, the group's size minus any left/top/right/bottom params passed
to DialogBackgroundCommons, not the group's size on its own.
"""

import os
import sys

from PIL import Image, ImageDraw

SCALE = 4
DEFAULT_RADIUS = 46
MASK_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "media", "masks")


def generate(name, width, height, radius=DEFAULT_RADIUS):
    full = Image.new("RGBA", (width, height), (255, 255, 255, 0))
    ImageDraw.Draw(full).rounded_rectangle(
        (0, 0, width - 1, height - 1), radius=radius, fill=(255, 255, 255, 255)
    )

    # Round up so the mask never lands a fraction of a pixel short of the panel.
    out_size = (-(-width // SCALE), -(-height // SCALE))
    mask = full.resize(out_size, Image.LANCZOS)

    path = os.path.join(MASK_DIR, "%s.png" % name)
    mask.save(path, optimize=True)
    return path, out_size


def main():
    if len(sys.argv) not in (4, 5):
        print(__doc__.strip())
        return 1

    name = sys.argv[1]
    width, height = int(sys.argv[2]), int(sys.argv[3])
    radius = int(sys.argv[4]) if len(sys.argv) == 5 else DEFAULT_RADIUS

    path, size = generate(name, width, height, radius)
    print("%s  %dx%d panel -> %dx%d mask (radius %d)" % (path, width, height, size[0], size[1], radius))
    return 0


if __name__ == "__main__":
    sys.exit(main())
