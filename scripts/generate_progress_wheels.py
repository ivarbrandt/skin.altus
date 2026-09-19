#!/usr/bin/env python3
"""Generate the progress wheel texture set (1.png - 100.png).

These are the per-percent wheels used by ProgressBadge for watched progress and
by the PVR row for EPG progress. The white sector is the REMAINING portion, so
the wheel drains as playback advances: N.png shows (100 - N)% white.

The elapsed wedge grows CLOCKWISE FROM 12 O'CLOCK, which is what the original
set did -- measured off the old textures, not guessed. Keep it that way or every
existing caller inverts.

Output matches the format the skin expects: 32x32, PNG mode P (8-bit colormap)
with a tRNS alpha array. Source-resolution RGBA files work but cost ~56x the
memory per texture, so everything here is rendered large and downsampled.

Usage:
    python3 generate_progress_wheels.py                 # render to ./wheels_out
    python3 generate_progress_wheels.py --preview       # contact sheet only
    python3 generate_progress_wheels.py --install       # write into media/progress/unwatched

Requires Pillow.
"""

import argparse
import os
import sys

from PIL import Image, ImageDraw

# --- the knobs -------------------------------------------------------------
# All radii are in final-texture pixels on a SIZE x SIZE canvas.

SIZE = 32           # output texture size, matches the existing set
SUPERSAMPLE = 16    # render at SIZE*SS then downsample; higher = smoother edges

RING_OUTER = 15.5   # outer edge of the border ring
RING_WIDTH = 2.5    # <-- BORDER THICKNESS. This is what ships. The original
                    # set measured ~1.2, which was too thin to read once the
                    # border alpha was raised to match the pie.
RING_ALPHA = 255    # border opacity 0-255; matches the pie so they read as one
                    # object. The original set used 170, which made the border
                    # look like a different colour once it got thick enough to
                    # notice. That was inherited from wherever the old textures
                    # came from, not a deliberate choice.

# The pie is anchored to the OUTER edge, not to the ring's inner edge, so
# thickening the border never shrinks the disc. The ring grows inward and the
# pie overlaps it -- which is why the border only reads in the empty sector.
# Measured off the original set: pie edge 14.5, ring outer 15.5.
PIE_INSET = 1.0     # pie radius = RING_OUTER - PIE_INSET
FILL_ALPHA = 255    # opacity of the remaining-time sector

PALETTE_COLORS = 28  # matches the 23-28 colours the original set used

# Textures are pure white and get tinted by colordiffuse at the call site,
# so colour lives in the skin XML, not here.
WHITE = (255, 255, 255)

# --- rendering -------------------------------------------------------------


def render(percent: int) -> Image.Image:
    """Render one wheel at SIZE x SIZE, RGBA."""
    ss = SUPERSAMPLE
    big = SIZE * ss
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    centre = (SIZE - 1) / 2.0

    def box(radius):
        return [
            (centre - radius) * ss,
            (centre - radius) * ss,
            (centre + radius) * ss,
            (centre + radius) * ss,
        ]

    # Border ring: a full circle outline, drawn first so the pie sits over it.
    # Pillow draws an outline INWARD from the bounding box, so passing
    # RING_OUTER puts the ring at [RING_OUTER - RING_WIDTH, RING_OUTER] --
    # anchored to the rim. Centring the box here instead sinks the ring
    # under the pie and the border vanishes.
    draw.ellipse(
        box(RING_OUTER),
        outline=WHITE + (RING_ALPHA,),
        width=max(1, round(RING_WIDTH * ss)),
    )

    # Remaining-time sector. Pillow measures angles from 3 o'clock, increasing
    # clockwise, so 12 o'clock is -90. The elapsed wedge occupies the first
    # percent*3.6 degrees clockwise from there; the white sector is the rest.
    sweep_start = -90.0 + percent * 3.6
    sweep_end = 270.0  # -90 + 360, i.e. back round to 12 o'clock
    if sweep_end - sweep_start > 0.01:
        pie_radius = RING_OUTER - PIE_INSET
        draw.pieslice(
            box(pie_radius),
            start=sweep_start,
            end=sweep_end,
            fill=WHITE + (FILL_ALPHA,),
        )

    return img.resize((SIZE, SIZE), Image.LANCZOS)


def palettise(img: Image.Image) -> Image.Image:
    """RGBA -> mode P with tRNS. FASTOCTREE is the method that keeps alpha."""
    return img.quantize(colors=PALETTE_COLORS, method=Image.FASTOCTREE)


def contact_sheet(images, cols=10, cell=64, pad=4):
    rows = (len(images) + cols - 1) // cols
    w = cols * (cell + pad) + pad
    h = rows * (cell + pad) + pad
    sheet = Image.new("RGBA", (w, h), (32, 40, 48, 255))
    for i, im in enumerate(images):
        big = im.convert("RGBA").resize((cell, cell), Image.NEAREST)
        x = pad + (i % cols) * (cell + pad)
        y = pad + (i // cols) * (cell + pad)
        sheet.alpha_composite(big, (x, y))
    return sheet.convert("RGB")


def main():
    global RING_WIDTH, RING_ALPHA

    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="wheels_out", help="output directory")
    ap.add_argument("--preview", action="store_true",
                    help="write a contact sheet instead of the texture set")
    ap.add_argument("--install", action="store_true",
                    help="write straight into media/progress/unwatched")
    ap.add_argument("--ring", type=float, default=None,
                    help=f"border thickness in px, overrides RING_WIDTH ({RING_WIDTH})")
    ap.add_argument("--alpha", type=int, default=None,
                    help=f"border opacity 0-255, overrides RING_ALPHA ({RING_ALPHA})")
    args = ap.parse_args()

    if args.ring is not None:
        RING_WIDTH = args.ring
    if args.alpha is not None:
        RING_ALPHA = args.alpha

    here = os.path.dirname(os.path.abspath(__file__))
    if args.install:
        out_dir = os.path.join(here, "..", "media", "progress", "unwatched")
    else:
        out_dir = os.path.join(here, args.out)
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    rendered = [render(n) for n in range(1, 101)]

    if args.preview:
        path = os.path.join(out_dir, "_preview.png")
        contact_sheet(rendered).save(path)
        print(f"preview -> {path}")
        return

    total = 0
    for n, img in enumerate(rendered, start=1):
        path = os.path.join(out_dir, f"{n}.png")
        palettise(img).save(path, optimize=True)
        total += os.path.getsize(path)

    print(f"wrote 100 textures -> {out_dir}")
    print(f"ring width {RING_WIDTH}px, alpha {RING_ALPHA}, total {total/1024:.1f} KB")


if __name__ == "__main__":
    sys.exit(main())
