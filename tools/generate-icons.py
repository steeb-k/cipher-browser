#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-only
"""Generate the Cipher Bridge icon set from a single keyhole definition.

State is carried by colour rather than by a corner badge: the brand pink when
the safe is open, dull grey when it is locked. Badges are kept only for the two states
colour alone cannot express -- disconnected and error -- because those are
failures the user needs to tell apart from a merely locked safe.

Firefox loads the SVGs (browserAction.js picks svg for Firefox and Safari, png
elsewhere), so the SVGs are the ones that matter here; PNGs are emitted for
Chromium and for the extension listing.

    tools/generate-icons.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ICONS = Path(__file__).resolve().parent.parent / "keepassxc-browser" / "icons"
TOOLBAR = ICONS / "toolbar"

# Matches the application icon, whose dominant colour is #fa68eb, and the value
# tools/rebrand-icons.sh already uses for the in-page icons. Keeping one brand
# colour across all three is the point.
BRAND = "#ff67ef"    # safe open
GREY = "#90949b"     # safe locked
RED = "#e5484d"      # disconnected
AMBER = "#f5a524"    # error
GREEN = "#30a46c"    # update available

# Monochrome toolbar themes. The directory name is the colour scheme the icon is
# FOR, not the colour it is drawn in -- browserAction.generateIconName passes
# retrieveColorScheme()'s answer straight through as the directory, and that
# returns "dark" when the browser is in dark mode. So "dark" holds the light
# icon. Getting this backwards paints a near-black icon onto a black toolbar,
# where it is invisible; the values below are upstream's, which had it right.
#
# Presented to the user as a single "Monochrome" choice; which of the two is
# used depends on the browser, so offering them separately would just be a way
# to pick the invisible one.
MONO = {"dark": "#fcfcfc", "light": "#0f0f0d"}

# Selectable icon colours. Every value except the brand pink is lifted from
# libadwaita's named palette (the -4 shades, extracted from its own gtk.css),
# which is what data/style.css already uses for entry labels in the application.
# Sharing the values means an icon set to Blue is the same blue as a Blue label,
# rather than two blues that nearly agree.
PALETTES = {
    "pink": BRAND,
    "blue": "#1c71d8",
    "green": "#2ec27e",
    "yellow": "#f5c211",
    "orange": "#e66100",
    "red": "#c01c28",
    "purple": "#813d9c",
    "brown": "#865e3c",
}

SIZE = 64

# Proportions taken from the application icon rather than invented, so the two
# read as the same mark. Measured on its 810px original and scaled to 64:
# keyhole centred at 28% of the width, 82% tall; arms 9% tall with their
# centres at 35% and 65%, starting at 60% and running off the right edge.
#
# Everything below is painted into a mask, black meaning cut away, so the
# keyhole and arms become real transparency -- the negative space the app icon
# uses -- rather than white shapes that would only look right on a light
# background.
BODY = '<rect x="1" y="1" width="62" height="62" rx="13" fill="white"/>'

KEYHOLE = (
    '<circle cx="18" cy="19.5" r="13.5" fill="black"/>'
    '<path d="M13.5 29 L10.5 58 H25.5 L22.5 29 Z" fill="black"/>'
)

# Deliberately overrun the right edge: the slots are open-ended in the app icon,
# not enclosed bars.
ARMS = (
    '<rect x="38" y="19.4" width="28" height="6" rx="3" fill="black"/>'
    '<rect x="38" y="38.6" width="28" height="6" rx="3" fill="black"/>'
)

# Badges sit over the keyhole, so each carries a ring in the page background
# colour to hold it apart from the shape underneath. Without it the badge and
# the silhouette merge into one blob at toolbar size.
def _badge(body: str, colour: str) -> str:
    return (
        f'<circle cx="49" cy="49" r="14.5" fill="#fff"/>'
        f'<circle cx="49" cy="49" r="12.5" fill="{colour}"/>{body}'
    )


BADGE_CROSS = _badge(
    '<path d="M44 44 L54 54 M54 44 L44 54" stroke="#fff" '
    'stroke-width="4" stroke-linecap="round" fill="none"/>',
    RED,
)

BADGE_BANG = _badge(
    '<path d="M49 42.5 V51" stroke="#fff" stroke-width="4" '
    'stroke-linecap="round"/>'
    '<circle cx="49" cy="55.5" r="2.4" fill="#fff"/>',
    AMBER,
)

BADGE_NEW = (
    f'<circle cx="52" cy="12" r="11" fill="#fff"/>'
    f'<circle cx="52" cy="12" r="9" fill="{GREEN}"/>'
)


def svg(colour: str, badge: str = "", new: bool = False) -> str:
    extra = (badge or "") + (BADGE_NEW if new else "")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE}" '
        f'height="{SIZE}" viewBox="0 0 {SIZE} {SIZE}">'
        f'<defs><mask id="cut">'
        f'<rect width="{SIZE}" height="{SIZE}" fill="black"/>'
        f"{BODY}{KEYHOLE}{ARMS}"
        f"</mask></defs>"
        f'<rect width="{SIZE}" height="{SIZE}" fill="{colour}" mask="url(#cut)"/>'
        f"{extra}</svg>\n"
    )


def variants(open_colour: str, locked_colour: str) -> dict[str, str]:
    """The nine toolbar states for one theme."""
    out = {}
    for prefix, new in (("icon_", False), ("icon_new_", True)):
        out[f"{prefix}normal"] = svg(open_colour, new=new)
        out[f"{prefix}locked"] = svg(locked_colour, new=new)
        out[f"{prefix}cross"] = svg(locked_colour, BADGE_CROSS, new=new)
        out[f"{prefix}bang"] = svg(open_colour, BADGE_BANG, new=new)
    # Legacy variant still referenced by generateIconName's iconType passthrough.
    out["icon_dark"] = svg(open_colour)
    return out


def rasterise(src: Path, dest: Path, width: int, height: int) -> None:
    subprocess.run(
        ["rsvg-convert", "-w", str(width), "-h", str(height), str(src), "-o", str(dest)],
        check=True,
    )


def main() -> int:
    if not shutil.which("rsvg-convert"):
        print("rsvg-convert is required", file=sys.stderr)
        return 1

    written = 0

    # "colored" is the directory the extension falls back to when no colour has
    # been chosen, so it stays and mirrors the brand pink.
    themes = {"colored": variants(BRAND, GREY)}

    # Every selectable colour changes only the unlocked state. Locked stays grey
    # throughout, because the point of the locked icon is to be distinguishable
    # at a glance -- if it followed the chosen colour it would differ from the
    # unlocked one only in ways the user just told us they like looking at.
    for name, colour in PALETTES.items():
        themes[name] = variants(colour, GREY)

    # Monochrome is single-colour by definition, so locked and open match.
    for name, colour in MONO.items():
        themes[name] = variants(colour, colour)

    for theme, icons in themes.items():
        directory = TOOLBAR / theme
        directory.mkdir(parents=True, exist_ok=True)
        for name, markup in icons.items():
            svg_path = directory / f"{name}.svg"
            svg_path.write_text(markup)
            rasterise(svg_path, directory / f"{name}.png", SIZE, SIZE)
            written += 2
        print(f"{theme}: {len(icons)} svg + {len(icons)} png")

    # In-field icons, drawn inside a text field by css/username.css. These
    # carry the KeePassXC logo but no brand green, so the colour substitution
    # in rebrand-icons.sh never touched them and they stayed KeePassXC-branded
    # long after everything else had changed.
    (ICONS / "locked.svg").write_text(svg(GREY))
    (ICONS / "disconnected.svg").write_text(svg(GREY, BADGE_CROSS))
    written += 2
    print("in-field: locked.svg, disconnected.svg")

    # Extension icon: the open-safe keyhole, used in about:addons and the
    # extension listing. Filename kept so no manifest or code reference moves.
    app_icon = ICONS / "keepassxc.svg"
    app_icon.write_text(svg(BRAND))
    written += 1

    for png in sorted(ICONS.glob("keepassxc_*.png")):
        size = png.stem.split("_")[-1]
        w, h = (int(v) for v in size.split("x"))
        rasterise(app_icon, png, w, h)
        written += 1
    print(f"app icon: keepassxc.svg + {len(list(ICONS.glob('keepassxc_*.png')))} png")

    print(f"\n{written} files written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
