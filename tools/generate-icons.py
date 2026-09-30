#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-only
"""Generate the Cipher Bridge icon set.

Three icons, three jobs:

  * The toolbar icon is the cipher wheel, painted in the colour chosen in
    Cipher and grey when the safe is locked -- exactly what the application's
    tray icon does, so the two match. The drawing is read from
    tools/artwork/cipher-symbolic.svg rather than re-declared here, for the
    same reason the application's own tray generator reads it: a second copy
    of the path data is a second thing to drift.

  * The in-field icons (username, TOTP, password generator) keep the keyhole
    family, since a small glyph in a text field wants a simpler shape than the
    wheel, but take the same colour. They are written once per colour so the
    content script can pick the set that matches.

  * The extension icon, as shown in about:addons and the add-on listing, is
    the application icon itself, copied from tools/artwork/cipher.svg.

State is carried by colour rather than by a corner badge: the chosen colour
when the safe is open, dull grey when it is locked. Badges are kept only for
the two states colour alone cannot express -- disconnected and error --
because those are failures the user needs to tell apart from a merely locked
safe.

Firefox loads the SVGs (browserAction.js picks svg for Firefox and Safari, png
elsewhere), so the SVGs are the ones that matter here; PNGs are emitted for
Chromium and for the extension listing.

Needs rsvg-convert (Debian: librsvg2-bin). Set RSVG_CONVERT to use another
command, for instance one inside a flatpak SDK.

    tools/generate-icons.py
"""

from __future__ import annotations

import math
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ICONS = ROOT / "keepassxc-browser" / "icons"
TOOLBAR = ICONS / "toolbar"
FIELD = ICONS / "field"
ARTWORK = ROOT / "tools" / "artwork"

# Copies of the application's own artwork. The application owns the drawing;
# these are refreshed by hand when it changes, since the two are separately
# packaged and cannot share a file.
APP_ICON = ARTWORK / "cipher.svg"
SYMBOLIC = ARTWORK / "cipher-symbolic.svg"

# Matches the application's tray icons and its brand pink.
BRAND = "#ff67ef"    # safe open
GREY = "#90949b"     # safe locked; the same grey the tray icon uses
RED = "#e5484d"      # disconnected
AMBER = "#f5a524"    # error
GREEN = "#30a46c"    # update available

# Monochrome themes. The directory name is the colour scheme the icon is FOR,
# not the colour it is drawn in -- browserAction.generateIconName passes
# retrieveColorScheme()'s answer straight through as the directory, and that
# returns "dark" when the browser is in dark mode. So "dark" holds the light
# icon. Getting this backwards paints a near-black icon onto a black toolbar,
# where it is invisible; the values below are upstream's, which had it right.
# The in-field set follows the same convention, keyed on the page's
# prefers-color-scheme by content/cipher-icons.js.
#
# Presented to the user as a single "Monochrome" choice; which of the two is
# used depends on the browser, so offering them separately would just be a way
# to pick the invisible one.
MONO = {"dark": "#fcfcfc", "light": "#0f0f0d"}

# Selectable icon colours. Every value except the brand pink is lifted from
# libadwaita's named palette (the -4 shades, extracted from its own gtk.css),
# which is what data/style.css already uses for entry labels in the application.
# Sharing the values means an icon set to Blue is the same blue as a Blue label,
# rather than two blues that nearly agree. Duplicated in the application's
# tools/generate-tray-icons.py; keep the two tables the same.
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

# The symbolic icon is drawn on a 16px grid; the toolbar set is written at 64.
WHEEL_SCALE = SIZE // 16

# ---------------------------------------------------------------- in-field --
#
# Everything below is painted into a mask, black meaning cut away, so the
# openings become real transparency rather than white shapes that would only
# look right on a light background.

# The keyhole, for username fields. Kept from the previous icon set: a small
# glyph beside a text field reads better as a keyhole than as the wheel, and
# it is what users of this extension already know.
BODY = '<rect x="1" y="1" width="62" height="62" rx="13" fill="white"/>'

KEYHOLE = (
    '<circle cx="18" cy="19.5" r="13.5" fill="black"/>'
    '<path d="M13.5 29 L10.5 58 H25.5 L22.5 29 Z" fill="black"/>'
)

# Deliberately overrun the right edge: the slots are open-ended, not enclosed
# bars.
ARMS = (
    '<rect x="38" y="19.4" width="28" height="6" rx="3" fill="black"/>'
    '<rect x="38" y="38.6" width="28" height="6" rx="3" fill="black"/>'
)

UNLOCK = BODY + KEYHOLE + ARMS


def _asterisk(cx: float, cy: float, arm: float = 7.5) -> str:
    """Three strokes through a centre, cut out of the mask."""
    lines = []
    for angle in (90, 30, 150):
        dx = arm * math.cos(math.radians(angle))
        dy = arm * math.sin(math.radians(angle))
        lines.append(
            f'<path d="M{cx - dx:.2f} {cy - dy:.2f} L{cx + dx:.2f} {cy + dy:.2f}" '
            'stroke="black" stroke-width="4" stroke-linecap="round"/>'
        )
    return "".join(lines)


# A speech bubble with three asterisks, for TOTP fields: the same idea as the
# icon upstream shipped, redrawn flat so it can be painted in one colour.
TOTP = (
    '<rect x="2" y="9" width="60" height="40" rx="10" fill="white"/>'
    '<path d="M42 47 L52 60 L54 47 Z" fill="white"/>'
    + _asterisk(17, 29) + _asterisk(32, 29) + _asterisk(47, 29)
)

# A key, for the password generator: bow on the left, shaft running right with
# two teeth.
KEY = (
    '<circle cx="18" cy="32" r="15" fill="white"/>'
    '<circle cx="18" cy="32" r="5.5" fill="black"/>'
    '<rect x="30" y="27.5" width="33" height="9" rx="2" fill="white"/>'
    '<rect x="46" y="34" width="6" height="11" fill="white"/>'
    '<rect x="56" y="34" width="6" height="14" fill="white"/>'
)

FIELD_ICONS = {"unlock": UNLOCK, "totp": TOTP, "key": KEY}

# ----------------------------------------------------------------- badges ----
#
# Badges sit bottom-left, over the thin part of the ring rather than over the
# handle, and each carries a ring in the page background colour to hold it
# apart from the shape underneath. Without it the badge and the wheel merge
# into one blob at toolbar size.
BADGE_X, BADGE_Y = 15, 49


def _badge(body: str, colour: str) -> str:
    return (
        f'<circle cx="{BADGE_X}" cy="{BADGE_Y}" r="14.5" fill="#fff"/>'
        f'<circle cx="{BADGE_X}" cy="{BADGE_Y}" r="12.5" fill="{colour}"/>{body}'
    )


BADGE_CROSS = _badge(
    f'<path d="M{BADGE_X - 5} {BADGE_Y - 5} L{BADGE_X + 5} {BADGE_Y + 5} '
    f'M{BADGE_X + 5} {BADGE_Y - 5} L{BADGE_X - 5} {BADGE_Y + 5}" stroke="#fff" '
    'stroke-width="4" stroke-linecap="round" fill="none"/>',
    RED,
)

BADGE_BANG = _badge(
    f'<path d="M{BADGE_X} {BADGE_Y - 6.5} V{BADGE_Y + 2}" stroke="#fff" '
    'stroke-width="4" stroke-linecap="round"/>'
    f'<circle cx="{BADGE_X}" cy="{BADGE_Y + 6.5}" r="2.4" fill="#fff"/>',
    AMBER,
)

BADGE_NEW = (
    f'<circle cx="52" cy="12" r="11" fill="#fff"/>'
    f'<circle cx="52" cy="12" r="9" fill="{GREEN}"/>'
)


def _svg_open() -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE}" '
        f'height="{SIZE}" viewBox="0 0 {SIZE} {SIZE}">'
    )


def masked_svg(shapes: str, colour: str, extra: str = "") -> str:
    """A single-colour glyph cut out of a mask."""
    return (
        _svg_open()
        + f'<defs><mask id="cut"><rect width="{SIZE}" height="{SIZE}" fill="black"/>'
        + shapes
        + "</mask></defs>"
        + f'<rect width="{SIZE}" height="{SIZE}" fill="{colour}" mask="url(#cut)"/>'
        + extra
        + "</svg>\n"
    )


def wheel_paths() -> list[str]:
    """The path data of the symbolic icon, in drawing order.

    Only the geometry is taken. The template paints every path in one fill,
    which is what makes re-colouring it a matter of one attribute on a group.
    """
    text = SYMBOLIC.read_text()
    paths = re.findall(r'<path\b[^>]*\bd="([^"]+)"', text)
    if not paths:
        raise SystemExit(f"{SYMBOLIC}: no <path d=...> elements found")
    return paths


def wheel_svg(paths: list[str], colour: str, badge: str = "", new: bool = False) -> str:
    body = "".join(f'<path d="{d}"/>' for d in paths)
    extra = (badge or "") + (BADGE_NEW if new else "")
    return (
        _svg_open()
        + f'<g fill="{colour}" transform="scale({WHEEL_SCALE})">{body}</g>'
        + extra
        + "</svg>\n"
    )


def toolbar_variants(paths: list[str], open_colour: str, locked_colour: str) -> dict[str, str]:
    """The nine toolbar states for one theme."""
    out = {}
    for prefix, new in (("icon_", False), ("icon_new_", True)):
        out[f"{prefix}normal"] = wheel_svg(paths, open_colour, new=new)
        out[f"{prefix}locked"] = wheel_svg(paths, locked_colour, new=new)
        out[f"{prefix}cross"] = wheel_svg(paths, locked_colour, BADGE_CROSS, new=new)
        out[f"{prefix}bang"] = wheel_svg(paths, open_colour, BADGE_BANG, new=new)
    # Legacy variant still referenced by generateIconName's iconType passthrough.
    out["icon_dark"] = wheel_svg(paths, open_colour)
    return out


def themes() -> dict[str, tuple[str, str]]:
    """Theme directory -> (open colour, locked colour).

    "colored" is the directory the extension falls back to when no colour has
    been chosen, so it stays and mirrors the brand pink.

    Every selectable colour changes only the unlocked state. Locked stays grey
    throughout, because the point of the locked icon is to be distinguishable
    at a glance -- if it followed the chosen colour it would differ from the
    unlocked one only in ways the user just told us they like looking at.

    Monochrome gets the same grey locked state as every other theme. It used
    to reuse its own colour for both, on the reasoning that a single-colour
    theme has nothing to switch to -- but that makes the locked icon identical
    to the unlocked one, so a user on Monochrome had no way to tell a locked
    safe from an open one. The grey is a mid tone by design, which is what
    lets it read against a white icon on a dark toolbar and against a
    near-black one on a light toolbar.
    """
    out = {"colored": (BRAND, GREY)}
    out.update({name: (colour, GREY) for name, colour in PALETTES.items()})
    out.update({name: (colour, GREY) for name, colour in MONO.items()})
    return out


def rsvg_command() -> list[str] | None:
    override = os.environ.get("RSVG_CONVERT")
    if override:
        return shlex.split(override)
    found = shutil.which("rsvg-convert")
    return [found] if found else None


def main() -> int:
    rsvg = rsvg_command()
    if rsvg is None:
        print(
            "rsvg-convert is required (Debian: apt install librsvg2-bin), "
            "or set RSVG_CONVERT to an equivalent command",
            file=sys.stderr,
        )
        return 1

    def rasterise(src: Path, dest: Path, width: int, height: int) -> None:
        subprocess.run(
            rsvg + ["-w", str(width), "-h", str(height), str(src), "-o", str(dest)],
            check=True,
        )

    for required in (APP_ICON, SYMBOLIC):
        if not required.exists():
            print(f"missing {required}", file=sys.stderr)
            return 1

    paths = wheel_paths()
    written = 0

    toolbar = {
        name: toolbar_variants(paths, open_colour, locked_colour)
        for name, (open_colour, locked_colour) in themes().items()
    }

    # A state the user cannot see is the same as one that never changes, and
    # that is not visible in the output -- the files are all present and all
    # well-formed, so the only symptom is a toolbar icon that appears to ignore
    # the safe. Monochrome shipped like that. Refuse to write a set where two
    # states a user is meant to tell apart are byte-identical.
    for theme, icons in toolbar.items():
        for a, b in (("icon_normal", "icon_locked"),
                     ("icon_new_normal", "icon_new_locked")):
            if icons[a] == icons[b]:
                print(
                    f"{theme}: {a} and {b} are identical, so a locked safe "
                    f"would look exactly like an open one",
                    file=sys.stderr,
                )
                return 1

    for theme, icons in toolbar.items():
        directory = TOOLBAR / theme
        directory.mkdir(parents=True, exist_ok=True)
        for name, markup in icons.items():
            svg_path = directory / f"{name}.svg"
            svg_path.write_text(markup)
            rasterise(svg_path, directory / f"{name}.png", SIZE, SIZE)
            written += 2
        print(f"toolbar/{theme}: {len(icons)} svg + {len(icons)} png")

    # In-field icons, one directory per theme, picked by content/cipher-icons.js
    # to match the colour Cipher sent. Only the open state is coloured; the
    # locked and disconnected keyholes below stay grey for the same reason the
    # locked toolbar icon does.
    for theme, (open_colour, _) in themes().items():
        directory = FIELD / theme
        directory.mkdir(parents=True, exist_ok=True)
        for name, shapes in FIELD_ICONS.items():
            (directory / f"{name}.svg").write_text(masked_svg(shapes, open_colour))
            written += 1
        print(f"field/{theme}: {len(FIELD_ICONS)} svg")

    (ICONS / "locked.svg").write_text(masked_svg(UNLOCK, GREY))
    (ICONS / "disconnected.svg").write_text(masked_svg(UNLOCK, GREY, BADGE_CROSS))
    written += 2

    # The files upstream's stylesheets name. css/cipher-icons.css overrides them
    # with the coloured set, so these are only ever seen if that override fails
    # to load -- in which case they should at least be ours, in the brand pink,
    # rather than the KeePassXC green drawings they replaced.
    (ICONS / "otp.svg").write_text(masked_svg(TOTP, BRAND))
    (ICONS / "key.svg").write_text(masked_svg(KEY, BRAND))
    written += 2
    print("in-field fallbacks: locked.svg, disconnected.svg, otp.svg, key.svg")

    # Extension icon: the application icon itself, so the add-on and the
    # application look like one product in about:addons and the listing.
    # Filename kept so no manifest or code reference moves.
    app_icon = ICONS / "keepassxc.svg"
    shutil.copyfile(APP_ICON, app_icon)
    written += 1

    pngs = sorted(ICONS.glob("keepassxc_*.png"))
    for png in pngs:
        w, h = (int(v) for v in png.stem.split("_")[-1].split("x"))
        rasterise(app_icon, png, w, h)
        written += 1
    print(f"extension icon: keepassxc.svg + {len(pngs)} png")

    print(f"\n{written} files written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
