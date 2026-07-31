#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
#
# Sign Cipher Bridge through addons.mozilla.org so it installs on release
# Firefox, which refuses unsigned add-ons outright.
#
#   tools/sign-xpi.sh --lint      # validate locally, upload nothing
#   tools/sign-xpi.sh             # upload and sign (unlisted)
#
# Unlisted channel: the add-on is signed for self-distribution and never
# appears in the public AMO gallery. Automated validation only.
#
# Credentials live in ~/.config/cipher/amo-credentials (mode 600), outside the
# repository so they cannot be committed. Regenerate them at
# https://addons.mozilla.org/developers/addon/api/key/ -- the secret is shown
# once, and rotating it is the cheapest response to it ever being exposed.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE="$ROOT/keepassxc-browser"
CREDENTIALS="${CIPHER_AMO_CREDENTIALS:-$HOME/.config/cipher/amo-credentials}"
ARTIFACTS="$ROOT/dist"

command -v web-ext >/dev/null || {
    echo "web-ext is required: npm i -g web-ext" >&2; exit 1; }

# Firefox needs the Manifest V2 variant; the working manifest is the MV3 one.
python3 "$ROOT/tools/stage-manifest.py" firefox >/dev/null

VERSION="$(python3 -c "import json;print(json.load(open('$SOURCE/manifest.json'))['version'])")"
NAME="$(python3 -c "import json;print(json.load(open('$SOURCE/manifest.json'))['name'])")"

if [ "${1:-}" = "--lint" ]; then
    echo "Linting $NAME $VERSION (nothing is uploaded)"
    web-ext lint --source-dir "$SOURCE"
    exit $?
fi

[ -f "$CREDENTIALS" ] || {
    echo "missing $CREDENTIALS" >&2; exit 1; }

# shellcheck source=/dev/null
. "$CREDENTIALS"

: "${AMO_JWT_ISSUER:?not set in $CREDENTIALS}"
: "${AMO_JWT_SECRET:?not set in $CREDENTIALS}"

cat <<WARN

About to upload $NAME $VERSION to addons.mozilla.org.

This is not reversible: AMO will never accept version $VERSION for this
add-on again, and the id in the manifest becomes bound to your account.
Bump the version in dist/manifest_firefox.json first if that is not what
you want.

WARN
read -r -p "Continue? [y/N] " reply
[ "$reply" = "y" ] || [ "$reply" = "Y" ] || { echo "Aborted."; exit 1; }

mkdir -p "$ARTIFACTS"

# Credentials are passed through the environment rather than argv, so they do
# not show up in the process list for every other user on the machine.
AMO_JWT_ISSUER="$AMO_JWT_ISSUER" \
AMO_JWT_SECRET="$AMO_JWT_SECRET" \
WEB_EXT_API_KEY="$AMO_JWT_ISSUER" \
WEB_EXT_API_SECRET="$AMO_JWT_SECRET" \
    web-ext sign \
        --source-dir "$SOURCE" \
        --artifacts-dir "$ARTIFACTS" \
        --channel unlisted

echo
echo "Signed artefacts in $ARTIFACTS"
echo "Install with about:addons -> gear -> Install Add-on From File."
