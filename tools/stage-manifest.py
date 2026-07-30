#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-only
"""Stage a per-browser manifest for loading the extension unpacked.

The checked-in working manifest (keepassxc-browser/manifest.json) is the
Manifest V3 / Chromium one, whose background section uses a service_worker.
Firefox does not support service_worker backgrounds, so loading the tree
as-is in Firefox fails. build.js only swaps manifests while packaging zips,
which is no help for `about:debugging` or `web-ext run`.

This stages the variant you want, preserving the original the same way
build.js does (as manifest_default.json) so it can be put back.

    tools/stage-manifest.py firefox      # prepare for Firefox
    tools/stage-manifest.py --restore    # put the working manifest back
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKING = ROOT / "keepassxc-browser" / "manifest.json"
BACKUP = ROOT / "manifest_default.json"

VARIANTS = {
    "firefox": ROOT / "dist" / "manifest_firefox.json",
    "chromium": ROOT / "dist" / "manifest_chromium.json",
}


def describe(path: Path) -> str:
    data = json.loads(path.read_text())
    background = data.get("background", {})
    kind = "service_worker" if "service_worker" in background else "scripts"
    gecko = (
        data.get("applications", {}).get("gecko")
        or data.get("browser_specific_settings", {}).get("gecko")
        or {}
    )
    return (
        f"name={data.get('name')!r} mv={data.get('manifest_version')} "
        f"background={kind} id={gecko.get('id', '(none)')}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("browser", nargs="?", choices=sorted(VARIANTS))
    parser.add_argument("--restore", action="store_true")
    args = parser.parse_args()

    if args.restore:
        if not BACKUP.exists():
            print(f"nothing to restore: {BACKUP} does not exist", file=sys.stderr)
            return 1
        shutil.move(BACKUP, WORKING)
        print(f"restored {WORKING.relative_to(ROOT)}")
        print(f"  {describe(WORKING)}")
        return 0

    if not args.browser:
        parser.error("give a browser, or --restore")

    source = VARIANTS[args.browser]
    if not source.exists():
        print(f"missing variant: {source}", file=sys.stderr)
        return 1

    # Only back up once, so repeated staging cannot lose the original.
    if not BACKUP.exists():
        shutil.copyfile(WORKING, BACKUP)
        print(f"saved original to {BACKUP.relative_to(ROOT)}")

    shutil.copyfile(source, WORKING)
    print(f"staged {source.relative_to(ROOT)} -> {WORKING.relative_to(ROOT)}")
    print(f"  {describe(WORKING)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
