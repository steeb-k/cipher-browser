#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-only
"""Apply Cipher Bridge identity to the extension manifests.

Every value changed here exists to keep this extension from colliding with a
KeePassXC-Browser install running side by side in the same browser:

  * the extension ID separates storage, permissions and the native host
    allowlist entry;
  * the name distinguishes the two in about:addons and the toolbar;
  * the keyboard shortcuts must differ because a browser silently drops a
    duplicate suggested_key, which would break shortcuts in whichever
    extension happened to load second.
  * the author and homepage are shown in about:addons and are where a user
    goes to report a problem, so they must name this fork, not upstream.

Re-runnable: applies cleanly to a freshly pulled upstream manifest.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

NAME = "Cipher Bridge"
EXTENSION_ID = "cipher-bridge@steeb-k.github.io"
AUTHOR = "steeb-k"
HOMEPAGE_URL = "https://github.com/steeb-k/cipher-browser"

MANIFESTS = [
    ROOT / "keepassxc-browser" / "manifest.json",
    ROOT / "dist" / "manifest_firefox.json",
    ROOT / "dist" / "manifest_chromium.json",
]

# Deliberately clear of KeePassXC-Browser's Alt+Shift+U/I/O/G.
SHORTCUTS = {
    "fill_username_password": ("Alt+Shift+C", "MacCtrl+Shift+C"),
    "fill_password": ("Alt+Shift+V", "MacCtrl+Shift+V"),
    "fill_totp": ("Alt+Shift+B", "MacCtrl+Shift+B"),
    "show_password_generator": ("Alt+Shift+N", "MacCtrl+Shift+N"),
}


def rebrand(path: Path) -> list[str]:
    data = json.loads(path.read_text())
    changes = []

    if data.get("name") != NAME:
        data["name"] = NAME
        changes.append("name")

    # Shown in about:addons and the store listing, so they must not say
    # KeePassXC Team and point at keepassxreboot: those are upstream's, and
    # this is where users would go to report a problem.
    for key, value in (("author", AUTHOR), ("homepage_url", HOMEPAGE_URL)):
        if data.get(key) != value:
            data[key] = value
            changes.append(key)

    # Firefox reads the ID from either key depending on manifest version.
    for key in ("applications", "browser_specific_settings"):
        gecko = data.get(key, {}).get("gecko")
        if gecko is not None and gecko.get("id") != EXTENSION_ID:
            gecko["id"] = EXTENSION_ID
            changes.append(f"{key}.gecko.id")

    commands = data.get("commands", {})
    for command, (default, mac) in SHORTCUTS.items():
        entry = commands.get(command)
        if entry is None or "suggested_key" not in entry:
            continue
        if entry["suggested_key"].get("default") != default:
            entry["suggested_key"]["default"] = default
            if "mac" in entry["suggested_key"]:
                entry["suggested_key"]["mac"] = mac
            changes.append(f"commands.{command}")

    if changes:
        path.write_text(json.dumps(data, indent=4) + "\n")

    return changes


def main() -> int:
    missing = [p for p in MANIFESTS if not p.exists()]
    if missing:
        for p in missing:
            print(f"missing: {p}", file=sys.stderr)
        return 1

    for path in MANIFESTS:
        changes = rebrand(path)
        rel = path.relative_to(ROOT)
        print(f"{rel}: {', '.join(changes) if changes else 'already current'}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
