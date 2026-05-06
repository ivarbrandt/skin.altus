#!/usr/bin/env python3
"""Generate iconpicker manifest JSON from the on-disk monochrome/ folder.

Walks <icons_dir> one level deep and writes {folder: [filename, ...]} to
<output_json>. The IconPickerDialog reads this manifest at runtime instead
of calling xbmcvfs.listdir(), so the loose iconpicker PNGs no longer need
to ship in the skin zip — Textures.xbt provides the rendering.
"""
import json
import os
import sys


def main():
    if len(sys.argv) != 3:
        print(
            "Usage: generate_iconpicker_manifest.py <icons_dir> <output_json>",
            file=sys.stderr,
        )
        sys.exit(1)
    icons_dir, output = sys.argv[1], sys.argv[2]
    if not os.path.isdir(icons_dir):
        print("ERROR: not a directory: %s" % icons_dir, file=sys.stderr)
        sys.exit(1)

    manifest = {}
    for entry in sorted(os.listdir(icons_dir)):
        sub = os.path.join(icons_dir, entry)
        if not os.path.isdir(sub):
            continue
        pngs = sorted(f for f in os.listdir(sub) if f.lower().endswith(".png"))
        if pngs:
            manifest[entry] = pngs

    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
    with open(output, "w") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)

    total = sum(len(v) for v in manifest.values())
    print("Wrote %s: %d folders, %d icons" % (output, len(manifest), total))


if __name__ == "__main__":
    main()
