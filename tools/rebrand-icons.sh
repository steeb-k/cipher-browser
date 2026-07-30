#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
#
# Recolour the extension icons from KeePassXC green to Cipher violet.
#
# Only the brand colours are substituted, so every shape, gradient and status
# variant (locked / cross / bang) survives untouched. Re-run this after pulling
# upstream icon changes.
#
# The monochrome dark/ and light/ toolbar variants are deliberately left alone:
# they are single-colour by design so they adapt to the toolbar theme, and
# recolouring them would defeat that. They are only used if the icon style
# setting is changed away from the 'colored' default.

set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
ICONS="$REPO/keepassxc-browser/icons"
UPSTREAM_REF="${UPSTREAM_REF:-upstream/develop}"

# KeePassXC brand green -> Cipher pink, sampled from the application icon:
# #ff67ef is its dominant colour, and the darker tone is the same hue at about
# 60% luminance, to keep the gradients readable.
LIGHT_FROM="#63ab3a"; LIGHT_TO="#ff67ef"
DARK_FROM="#226e23";  DARK_TO="#993e8f"

command -v rsvg-convert >/dev/null || { echo "rsvg-convert is required" >&2; exit 1; }

# Reset to pristine upstream artwork before substituting. Without this the
# script is a no-op on a second run and after any colour change: the greens it
# looks for were already replaced, so nothing matches and the icons silently
# keep whatever colour they had.
echo "Restoring upstream icons from $UPSTREAM_REF"
git -C "$REPO" checkout "$UPSTREAM_REF" -- keepassxc-browser/icons

recolour() {
    sed -i "s/${LIGHT_FROM}/${LIGHT_TO}/gI; s/${DARK_FROM}/${DARK_TO}/gI" "$1"
}

echo "Recolouring SVGs"
# Every SVG in the icon root plus the coloured toolbar set. Substitution is a
# no-op on files that do not use the brand colours, so this needs no allowlist
# and will pick up any icon upstream adds later.
for svg in "$ICONS"/*.svg "$ICONS"/toolbar/colored/*.svg; do
    [ -f "$svg" ] || continue
    recolour "$svg"
    echo "  ${svg#"$ICONS"/}"
done

echo "Rasterising application icons"
for png in "$ICONS"/keepassxc_*.png; do
    # Size lives in the filename, e.g. keepassxc_32x32.png
    name="$(basename "$png")"
    size="${name#keepassxc_}"; size="${size%.png}"
    w="${size%x*}"; h="${size#*x}"
    rsvg-convert -w "$w" -h "$h" "$ICONS/keepassxc.svg" -o "$png"
    echo "  $name (${w}x${h})"
done

echo "Rasterising coloured toolbar icons"
for svg in "$ICONS"/toolbar/colored/*.svg; do
    png="${svg%.svg}.png"
    [ -f "$png" ] || continue
    # Match whatever size the existing PNG used. Command substitution rather
    # than `read`, which returns non-zero on unterminated output and would
    # abort the script under `set -e`.
    size="$(identify -format "%wx%h" "$png")"
    w="${size%x*}"; h="${size#*x}"
    rsvg-convert -w "$w" -h "$h" "$svg" -o "$png"
    echo "  $(basename "$png") (${w}x${h})"
done

echo
echo "Done. Filenames are intentionally unchanged so that no reference in the"
echo "code or manifests can be missed; rename them during the UI rework."
