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
#
# Restricted to the in-page icons this script owns. Restoring the whole icons
# directory would also revert the application icon and the entire toolbar set,
# which tools/generate-icons.py draws from scratch -- running this script would
# silently throw that artwork away.
# locked.svg and disconnected.svg are deliberately absent: they are drawn from
# scratch by tools/generate-icons.py, because they carry the KeePassXC logo
# without using the brand green, so recolouring alone left them unchanged.
IN_PAGE=(
    custom_login_fields.svg
    help.svg
    key.svg
    otp.svg
)

echo "Restoring in-page icons from $UPSTREAM_REF"
for name in "${IN_PAGE[@]}"; do
    git -C "$REPO" checkout "$UPSTREAM_REF" -- "keepassxc-browser/icons/$name"
done

recolour() {
    sed -i "s/${LIGHT_FROM}/${LIGHT_TO}/gI; s/${DARK_FROM}/${DARK_TO}/gI" "$1"
}

echo "Recolouring SVGs"
# In-page icons only. The application icon and the whole toolbar set are
# generated from scratch by tools/generate-icons.py and must not be touched
# here: both scripts would otherwise rewrite the same files and the result
# would depend on which ran last.
for svg in "$ICONS"/*.svg; do
    [ -f "$svg" ] || continue
    case "$(basename "$svg")" in
        keepassxc.svg) continue ;;
    esac
    recolour "$svg"
    echo "  ${svg#"$ICONS"/}"
done

echo
echo "Done. Filenames are intentionally unchanged so that no reference in the"
echo "code or manifests can be missed; rename them during the UI rework."
echo "For the application and toolbar icons, run tools/generate-icons.py."
