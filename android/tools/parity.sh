#!/usr/bin/env bash
# Prove the Android encoder and nfcraft/ndef.py produce the same bytes, and
# that the pruned write plan still ends at those bytes.
#
# Ndef.java has no Android dependencies, so it compiles and runs on a desktop
# JVM. Both sides print area bytes, the page-by-page write plan, the strict
# decode round trip, emptiness and the occupied-region guard for the same
# inputs; any divergence shows up as a diff. PlanTest then checks the pruning
# that decides which of those pages actually travel over the radio.
#
# Usage: tools/parity.sh   (from the Android app directory)
#
# JAVA_HOME selects the JDK, PYTHON the interpreter, and NFCRAFT_ROOT the
# checkout holding nfcraft/ndef.py. Each is discovered when not set.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
root="$(cd "$here/.." && pwd)"
nfcraft="${NFCRAFT_ROOT:-$(cd "$root/.." && pwd)}"
[ -f "$nfcraft/nfcraft/ndef.py" ] || nfcraft="$(cd "$root/../.." && pwd)"
out="$(mktemp -d)"
trap 'rm -rf "$out"' EXIT

if [ -n "${JAVA_HOME:-}" ]; then
    javac="$JAVA_HOME/bin/javac"
    java="$JAVA_HOME/bin/java"
else
    javac="javac"
    java="java"
fi

python="${PYTHON:-$nfcraft/.venv/Scripts/python.exe}"
[ -x "$python" ] || python="${PYTHON:-python}"

if [ ! -f "$nfcraft/nfcraft/ndef.py" ]; then
    echo "Cannot find nfcraft/ndef.py. Set NFCRAFT_ROOT to the checkout holding it." >&2
    exit 2
fi

mkdir -p "$out/src/best/tgs/cardwriter"
cp "$root/app/src/main/java/best/tgs/cardwriter/Ndef.java" "$out/src/best/tgs/cardwriter/"
cp "$here/best/tgs/cardwriter/Harness.java" "$out/src/best/tgs/cardwriter/"
cp "$here/best/tgs/cardwriter/PlanTest.java" "$out/src/best/tgs/cardwriter/"
cp "$root/app/src/main/java/best/tgs/cardwriter/Tag215.java" "$out/src/best/tgs/cardwriter/"
cp "$here/best/tgs/cardwriter/LinkTest.java" "$out/src/best/tgs/cardwriter/"
mkdir -p "$out/src/android/nfc/tech"
cp "$here/stub/android/nfc/tech/NfcA.java" "$out/src/android/nfc/tech/"

"$javac" -d "$out/classes" -sourcepath "$out/src" \
    "$out/src/android/nfc/tech/NfcA.java" \
    "$out/src/best/tgs/cardwriter/Ndef.java" \
    "$out/src/best/tgs/cardwriter/Tag215.java" \
    "$out/src/best/tgs/cardwriter/Harness.java" \
    "$out/src/best/tgs/cardwriter/PlanTest.java" \
    "$out/src/best/tgs/cardwriter/LinkTest.java"
"$java" -cp "$out/classes" best.tgs.cardwriter.Harness > "$out/java.txt"

NFCRAFT_ROOT="$nfcraft" PYTHONIOENCODING=utf-8 "$python" "$here/ref.py" > "$out/python.txt"

if ! diff -u "$out/python.txt" "$out/java.txt"; then
    echo "FAIL: the encoders diverged. Do not write cards until this is resolved." >&2
    exit 1
fi
echo "PASS: the Android encoder matches nfcraft/ndef.py byte for byte."

"$java" -cp "$out/classes" best.tgs.cardwriter.PlanTest
"$java" -cp "$out/classes" best.tgs.cardwriter.LinkTest
