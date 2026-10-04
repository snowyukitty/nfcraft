#!/usr/bin/env bash
# Check the iPhone writer's platform-neutral core without a Mac:
#   1. `swift test` for NfcraftKit (encoder, pruned plan, link, framing,
#      presentation and history checks against a simulated NTAG215);
#   2. byte parity between the Swift encoder and nfcraft/ndef.py over
#      ios/tools/parity-cases.json.
#
# Uses a native `swift` when one is on PATH; otherwise the official
# swift:6.1-noble Docker image (SWIFT_IMAGE overrides it). Build products stay
# inside the container. Nothing here touches Core NFC, a phone or a card, so a
# pass is simulation evidence only — never iPhone NFC evidence.
#
# Usage: ios/tools/check.sh   (from anywhere)
# PYTHON selects the interpreter for the Python reference.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
repo="$(cd "$here/../.." && pwd)"
image="${SWIFT_IMAGE:-swift:6.1-noble}"
out="$(mktemp -d)"
trap 'rm -rf "$out"' EXIT

# The first interpreter that really is Python 3.11+. (On Windows a `python3`
# on PATH can be the Store alias, which prints nothing and runs nothing.)
python=""
for candidate in ${PYTHON:-} "$repo/.venv/Scripts/python.exe" "$repo/.venv/bin/python" python python3; do
    if "$candidate" -c 'import sys; sys.exit(sys.version_info < (3, 11))' >/dev/null 2>&1; then
        python="$candidate"
        break
    fi
done
[ -n "$python" ] || { echo "Python 3.11+ is required for the reference encoder." >&2; exit 2; }

if command -v swift >/dev/null 2>&1; then
    run_swift() { (cd "$repo/ios/NfcraftKit" && swift "$@"); }
    cases="$repo/ios/tools/parity-cases.json"
else
    command -v docker >/dev/null 2>&1 || { echo "Neither swift nor docker is available." >&2; exit 2; }
    mount="$repo"
    if command -v cygpath >/dev/null 2>&1; then mount="$(cygpath -m "$repo")"; fi
    # The named volume only caches build products; `docker volume rm
    # nfcraftkit-build` discards it.
    run_swift() {
        local sub="$1"; shift
        if [ "$sub" != "--version" ]; then set -- --scratch-path /build "$@"; fi
        MSYS_NO_PATHCONV=1 docker run --rm -v "$mount:/src:ro" -v nfcraftkit-build:/build \
            -w /src/ios/NfcraftKit "$image" swift "$sub" "$@"
    }
    cases="/src/ios/tools/parity-cases.json"
fi

run_swift --version 2>/dev/null | head -1 || true

run_swift test
run_swift run -c debug nfcraft-parity "$cases" > "$out/swift.txt"

NFCRAFT_ROOT="$repo" PYTHONIOENCODING=utf-8 "$python" "$here/ref.py" "$here/parity-cases.json" > "$out/python.txt"

if ! diff -u "$out/python.txt" "$out/swift.txt"; then
    echo "FAIL: the Swift encoder diverged from nfcraft/ndef.py. Do not write cards until this is resolved." >&2
    exit 1
fi
echo "PASS: the Swift encoder matches nfcraft/ndef.py byte for byte ($(wc -l < "$out/python.txt") lines)."
