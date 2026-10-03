#!/usr/bin/env python3
"""One-off: subsets the fonts embedded in the profile SVGs into assets/fonts/*.woff2.

GitHub renders README images as <img>, which can't load external fonts, so generate.py
inlines these small Latin subsets as base64 @font-face rules. Both fonts are SIL OFL 1.1
(licenses kept next to the files). Needs fonttools + brotli:

    pip install fonttools brotli
    python scripts/build_fonts.py path/to/Geist[wght].ttf ~/Library/Fonts/JetBrainsMono-Regular.ttf
"""
import os
import sys

from fontTools import subset

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "fonts")
UNICODES = (
    list(range(0x20, 0x7F)) + list(range(0xA0, 0x100))
    + [0x03BB, 0x2013, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D, 0x2022, 0x2026, 0x2192, 0x2197, 0x2713, 0x258D, 0x25CF]
)


def build(src, name):
    options = subset.Options()
    options.flavor = "woff2"
    options.layout_features = ["kern", "liga", "calt", "tnum"]
    options.hinting = False
    options.desubroutinize = True
    options.name_IDs = [1, 2]
    font = subset.load_font(src, options)
    subsetter = subset.Subsetter(options)
    subsetter.populate(unicodes=UNICODES)
    subsetter.subset(font)
    dst = os.path.join(OUT, name)
    subset.save_font(font, dst, options)
    print(f"{name}: {os.path.getsize(dst) // 1024} KB")


if __name__ == "__main__":
    geist, mono = sys.argv[1:3]
    os.makedirs(OUT, exist_ok=True)
    build(geist, "geist.woff2")  # variable: wght 100-900
    build(mono, "jetbrains-mono.woff2")
