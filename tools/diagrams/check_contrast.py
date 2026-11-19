#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prove every key-letter colour pair clears WCAG AA (4.5:1).

    python check_contrast.py        # prints the table, exits 1 if any pair fails

Run this after changing the key palette in diagram_style.py. Colour is never the only signal in
these diagrams - the letter always is - but the letter still has to be readable on its circle.
"""
import sys

from diagram_style import KEY_COLOURS


def luminance(h):
    c = [int(h[i:i + 2], 16) / 255.0 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def ratio(a, b):
    la, lb = luminance(a), luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def main():
    worst, failed = 99.0, []
    print("key  fill      ink       ratio")
    for letter, (fill, ink) in KEY_COLOURS.items():
        r = ratio(fill, ink)
        worst = min(worst, r)
        if r < 4.5:
            failed.append(letter)
        print(" %s   %s   %s   %5.1f:1%s"
              % (letter, fill, ink, r, "   <-- FAILS AA" if r < 4.5 else ""))
    print("\nworst pair: %.1f:1 (WCAG AA needs 4.5:1)" % worst)
    if failed:
        print("FAILED: %s" % ", ".join(failed))
        return 1
    print("all %d pairs pass" % len(KEY_COLOURS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
