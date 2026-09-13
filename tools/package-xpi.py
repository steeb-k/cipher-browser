#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-only
"""Package Cipher Bridge as an XPI for Firefox.

An XPI is a plain zip with manifest.json at the archive root, so this stages
the Firefox (Manifest V2) variant, zips the extension directory, and puts the
working manifest back.

Written rather than reusing build.js because that shells out to
`tar -a -cf out.zip`, and GNU tar cannot create zip archives at all -- only
bsdtar can. It also insists on pulling translations from Transifex first.

    tools/package-xpi.py             -> dist/cipher-bridge-<version>.xpi
    tools/package-xpi.py --out FILE  -> write somewhere else

Installing the result permanently needs a Firefox that accepts unsigned
add-ons; see the note printed at the end.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "keepassxc-browser"
WORKING_MANIFEST = SOURCE / "manifest.json"
BACKUP = ROOT / "manifest_default.json"
FIREFOX_MANIFEST = ROOT / "dist" / "manifest_firefox.json"

# Nothing here belongs in a shipped add-on.
EXCLUDE_DIRS = {"__pycache__", ".git", "node_modules"}
EXCLUDE_SUFFIXES = {".pyc", ".map"}


def iter_files(base: Path):
    for path in sorted(base.rglob("*")):
        if path.is_dir():
            continue

        parts = path.relative_to(base).parts
        if any(part in EXCLUDE_DIRS for part in parts):
            continue
        if path.suffix in EXCLUDE_SUFFIXES:
            continue

        # Dotfiles, as web-ext excludes them. Signing leaves .amo-upload-uuid in
        # the source directory, and shipping it puts an AMO upload identifier
        # inside the add-on every user installs. Nothing the extension loads at
        # runtime is a dotfile, so excluding the lot is safe and stays safe as
        # more tooling drops its state here.
        if any(part.startswith(".") for part in parts):
            continue

        yield path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    for required in (SOURCE, FIREFOX_MANIFEST):
        if not required.exists():
            print(f"missing {required}", file=sys.stderr)
            return 1

    manifest = json.loads(FIREFOX_MANIFEST.read_text())
    version = manifest.get("version", "0")
    gecko = manifest.get("applications", {}).get("gecko", {})

    out = args.out or (ROOT / "dist" / f"cipher-bridge-{version}.xpi")
    out.parent.mkdir(parents=True, exist_ok=True)

    # Stage the Firefox manifest, exactly as build.js does when packaging, and
    # always put the original back -- otherwise a failure here would leave the
    # checkout with the wrong manifest in place.
    restore = False
    if not BACKUP.exists():
        shutil.copyfile(WORKING_MANIFEST, BACKUP)
        restore = True
    shutil.copyfile(FIREFOX_MANIFEST, WORKING_MANIFEST)

    try:
        count = 0
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in iter_files(SOURCE):
                # Relative to SOURCE, so manifest.json lands at the archive
                # root. Nested one level down and Firefox rejects the file.
                archive.write(path, path.relative_to(SOURCE).as_posix())
                count += 1
    finally:
        if restore:
            shutil.move(BACKUP, WORKING_MANIFEST)

    size = out.stat().st_size
    print(f"wrote {out}")
    print(f"  {count} files, {size / 1024:.0f} KiB")
    print(f"  name    {manifest.get('name')}")
    print(f"  version {version}")
    print(f"  id      {gecko.get('id', '(none)')}")
    print(f"  manifest_version {manifest.get('manifest_version')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
