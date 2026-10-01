#!/usr/bin/env bash
# SPDX-License-Identifier: GPL-3.0-only
#
# Submit Cipher Bridge to addons.mozilla.org, which signs it so it installs
# on release Firefox.
#
#   tools/sign-xpi.sh lint        # validate locally, upload nothing
#   tools/sign-xpi.sh listed      # submit to the public AMO listing
#   tools/sign-xpi.sh unlisted    # sign for self-distribution only
#
# listed: the version is published on addons.mozilla.org once Mozilla has
# reviewed it, and Firefox then updates installed copies by itself. The first
# listed submission creates the listing from tools/amo-metadata.json; later
# ones only add a version to it. unlisted: signed for distribution outside
# AMO, no listing, automated review only.
#
# Both upload the repository as source alongside the package. The package
# contains minified third-party libraries, and a reviewer who can see where
# they came from does not have to ask.
#
# web-ext is used from the project's devDependencies (npm ci), or from PATH if
# installed globally. Credentials live in ~/.config/cipher/amo-credentials
# (mode 600), outside the repository so they cannot be committed:
#
#   AMO_JWT_ISSUER=user:12345:678
#   AMO_JWT_SECRET=...
#
# Generate them at https://addons.mozilla.org/developers/addon/api/key/ -- the
# secret is shown once, and rotating it is the cheapest response to it ever
# being exposed.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE="$ROOT/keepassxc-browser"
CREDENTIALS="${CIPHER_AMO_CREDENTIALS:-$HOME/.config/cipher/amo-credentials}"
ARTIFACTS="$ROOT/dist"
METADATA="$ROOT/tools/amo-metadata.json"

MODE="${1:-}"
case "$MODE" in
    lint|listed|unlisted) ;;
    *) sed -n '4,10p' "$0" >&2; exit 2 ;;
esac

if command -v web-ext >/dev/null; then
    WEB_EXT=(web-ext)
elif [ -x "$ROOT/node_modules/.bin/web-ext" ]; then
    WEB_EXT=("$ROOT/node_modules/.bin/web-ext")
else
    echo "web-ext is required: run 'npm ci' in $ROOT, or 'npm i -g web-ext'" >&2
    exit 1
fi

# Firefox needs the Manifest V2 variant; stage it, and always put the working
# manifest back, whatever happens below.
python3 "$ROOT/tools/stage-manifest.py" firefox >/dev/null
restore() { python3 "$ROOT/tools/stage-manifest.py" --restore >/dev/null; }
trap restore EXIT

VERSION="$(python3 -c "import json;print(json.load(open('$SOURCE/manifest.json'))['version'])")"
NAME="$(python3 -c "import json;print(json.load(open('$SOURCE/manifest.json'))['name'])")"

if [ "$MODE" = lint ]; then
    echo "Linting $NAME $VERSION (nothing is uploaded)"
    "${WEB_EXT[@]}" lint --source-dir "$SOURCE"
    exit $?
fi

[ -f "$CREDENTIALS" ] || {
    echo "missing $CREDENTIALS" >&2; exit 1; }

# shellcheck source=/dev/null
. "$CREDENTIALS"

: "${AMO_JWT_ISSUER:?not set in $CREDENTIALS}"
: "${AMO_JWT_SECRET:?not set in $CREDENTIALS}"

if [ -n "$(git -C "$ROOT" status --porcelain --untracked-files=no)" ]; then
    echo "The checkout has uncommitted changes. The source archive uploaded" >&2
    echo "to AMO is the committed tree, so commit first or stash." >&2
    exit 1
fi

cat <<WARN

About to submit $NAME $VERSION to addons.mozilla.org on the $MODE channel.

This is not reversible: AMO will never accept version $VERSION for this
add-on again, on either channel, and the id in the manifest becomes bound to
your account. Bump the version in the manifests first if that is not what
you want.

WARN
read -r -p "Continue? [y/N] " reply
[ "$reply" = "y" ] || [ "$reply" = "Y" ] || { echo "Aborted."; exit 1; }

mkdir -p "$ARTIFACTS"

# The source reviewers see: the committed tree, which is exactly what the
# package was built from (nothing is transpiled or bundled).
SOURCE_ZIP="$ARTIFACTS/cipher-bridge-$VERSION-source.zip"
git -C "$ROOT" archive --format=zip -o "$SOURCE_ZIP" HEAD

ARGS=(
    sign
    --source-dir "$SOURCE"
    --artifacts-dir "$ARTIFACTS"
    --channel "$MODE"
    --upload-source-code "$SOURCE_ZIP"
    # Review of a listed submission takes days, not minutes; do not sit here
    # waiting for it. The XPI is downloaded from AMO once approved.
    --approval-timeout 0
)
if [ "$MODE" = listed ]; then
    # Harmless on a later version: AMO applies the listing fields to the
    # add-on and the version block to the new version.
    ARGS+=(--amo-metadata "$METADATA")
fi

# Credentials are passed through the environment rather than argv, so they do
# not show up in the process list for every other user on the machine.
WEB_EXT_API_KEY="$AMO_JWT_ISSUER" \
WEB_EXT_API_SECRET="$AMO_JWT_SECRET" \
    "${WEB_EXT[@]}" "${ARGS[@]}"

echo
case "$MODE" in
    listed)
        echo "Submitted. Track the review at"
        echo "  https://addons.mozilla.org/developers/addons"
        echo "Once approved, the listing is live and Firefox updates installed"
        echo "copies on its own. Future releases: bump the version, commit, and"
        echo "run 'tools/sign-xpi.sh listed' again."
        ;;
    unlisted)
        echo "Signed artefacts in $ARTIFACTS"
        echo "Install with about:addons -> gear -> Install Add-on From File."
        ;;
esac
