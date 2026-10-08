"""Check local mobile artifacts; never uploads or claims physical/store readiness.

Run after Gradle's tests/lint/assembleDebug/bundleRelease. Signed-bundle mode
requires the independently recorded upload certificate fingerprint. Passwords
and private keys are never accepted or read by this tool.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import struct
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ANDROID = Path(__file__).resolve().parents[1]
ROOT = ANDROID.parent
NS = "{http://schemas.android.com/apk/res/android}"


def png_info(path: Path) -> tuple[int, int, int]:
    with path.open("rb") as stream:
        header = stream.read(33)
    if len(header) != 33 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError("Invalid PNG header")
    width, height, depth, color = struct.unpack(">IIBB", header[16:26])
    if depth != 8 or color not in (2, 6):
        raise ValueError("Expected an 8-bit RGB/RGBA PNG")
    return width, height, color


def archive_info(path: Path) -> dict:
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError("Archive integrity check failed")
        names = archive.namelist()
        if path.suffix == ".aab":
            required = {"BundleConfig.pb", "base/manifest/AndroidManifest.xml", "base/dex/classes.dex"}
        else:
            required = {"AndroidManifest.xml", "classes.dex"}
        if not required.issubset(names):
            raise ValueError("Required Android package entries are missing")
        native = [name for name in names if name.endswith(".so")]
        if native:
            raise ValueError("Native libraries require separate ABI/16 KB page-size qualification")
        signature = any(name.upper().startswith("META-INF/") and
                        name.upper().endswith((".RSA", ".DSA", ".EC")) for name in names)
    return {"bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "native_library_count": len(native),
            "jar_signature_entries_present": signature}


def normalize_fingerprint(value: str) -> str:
    value = value.replace(":", "").replace(" ", "").upper()
    if not re.fullmatch(r"[0-9A-F]{64}", value):
        raise ValueError("Expected a SHA-256 certificate fingerprint (64 hex digits)")
    return value


def verified_signature(bundle: Path, expected: str) -> bool:
    jarsigner, keytool = shutil.which("jarsigner"), shutil.which("keytool")
    if not jarsigner or not keytool:
        raise ValueError("JDK jarsigner and keytool must be on PATH")
    result = subprocess.run([jarsigner, "-J-Duser.language=en", "-J-Duser.country=US",
                             "-verify", str(bundle)], capture_output=True, text=True, check=False)
    # jarsigner exits zero even for an unsigned archive: test the verified result too.
    if result.returncode != 0 or "jar verified." not in result.stdout:
        return False
    cert = subprocess.run([keytool, "-J-Duser.language=en", "-J-Duser.country=US",
                           "-printcert", "-jarfile", str(bundle)],
                          capture_output=True, text=True, check=False)
    fingerprints = re.findall(r"SHA256:\s*([0-9A-F:]+)", cert.stdout)
    return cert.returncode == 0 and len(fingerprints) == 1 and (
        normalize_fingerprint(fingerprints[0]) == normalize_fingerprint(expected))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aapt2", type=Path, default=ROOT / ".local/android-sdk/build-tools/35.0.0/aapt2.exe")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-signed", action="store_true")
    parser.add_argument("--upload-certificate-sha256")
    args = parser.parse_args()
    failures: list[str] = []
    checks: dict = {}

    def check(label, operation):
        try:
            value = operation()
            checks[label] = value
        except (OSError, ValueError, zipfile.BadZipFile, ET.ParseError, AssertionError) as error:
            failures.append(label)
            checks[label] = {"status": "FAIL", "reason": str(error)}

    apk = ANDROID / "app/build/outputs/apk/debug/app-debug.apk"
    aab = ANDROID / "app/build/outputs/bundle/release/app-release.aab"
    for name, path in (("debug_apk", apk), ("release_aab", aab)):
        check(name, lambda path=path: archive_info(path))

    def metadata():
        result = subprocess.run([str(args.aapt2), "dump", "badging", str(apk)],
                                capture_output=True, text=True, encoding="utf-8", check=True)
        source = (ANDROID / "app/build.gradle.kts").read_text(encoding="utf-8")
        code = re.search(r"versionCode = (\d+)", source).group(1)
        version = re.search(r'versionName = "([^"]+)"', source).group(1)
        required = ["name='best.tgs.cardwriter'", f"versionCode='{code}'",
                    f"versionName='{version}'", "application-label:'nfcraft'", "targetSdkVersion:'36'", "minSdkVersion:'21'"]
        assert all(item in result.stdout for item in required), "APK metadata does not match release source"
        permissions = set(re.findall(r"uses-permission: name='([^']+)'", result.stdout))
        assert permissions == {"android.permission.NFC", "android.permission.VIBRATE"}, "Unexpected APK permissions"
        return {"package": "best.tgs.cardwriter", "version": version, "version_code": int(code),
                "permissions": sorted(permissions)}

    try:
        check("apk_metadata", metadata)
    except subprocess.CalledProcessError:
        failures.append("apk_metadata")
        checks["apk_metadata"] = {"status": "FAIL", "reason": "aapt2 rejected the APK"}

    def asset(name, dimensions, rgb=False):
        width, height, color = png_info(ANDROID / "store" / name)
        assert (width, height) == dimensions, "Wrong store image dimensions"
        assert not rgb or color == 2, "Feature graphic must have no alpha channel"
        return {"dimensions": [width, height], "color_type": color}

    check("play_icon", lambda: asset("google-play-icon.png", (512, 512)))
    check("feature_graphic", lambda: asset("feature-graphic.png", (1024, 500), True))

    def unit_results():
        reports = sorted((ANDROID / "app/build/test-results/testDebugUnitTest").glob("TEST-*.xml"))
        assert reports, "No Android unit test reports; run Gradle first"
        total = 0
        for path in reports:
            suite = ET.parse(path).getroot()
            assert int(suite.get("failures", "0")) == 0 and int(suite.get("errors", "0")) == 0, "Unit tests failed"
            assert int(suite.get("skipped", "0")) == 0, "Unit tests were skipped"
            total += int(suite.get("tests", "0"))
        return {"tests": total, "scope": "local JVM/Robolectric; no physical NFC proof"}

    check("unit_results", unit_results)
    def lint_results():
        report = ET.parse(ANDROID / "app/build/reports/lint-results-debug.xml").getroot()
        issues = report.findall("issue")
        errors = sum(i.get("severity") in ("Error", "Fatal") for i in issues)
        warnings = sum(i.get("severity") == "Warning" for i in issues)
        assert errors == 0, "Android lint reports errors"
        return {"errors": errors, "warnings": warnings}
    check("lint", lint_results)

    signed = False
    if args.require_signed or args.upload_certificate_sha256:
        def signing():
            assert args.upload_certificate_sha256, "Provide the independently recorded upload certificate SHA-256"
            assert verified_signature(aab, args.upload_certificate_sha256), "Bundle is unsigned, invalid, or signed by a different certificate"
            return {"verified_against_expected_certificate": True}
        check("upload_signature", signing)
        signed = checks.get("upload_signature", {}).get("verified_against_expected_certificate", False)

    report = {
        "status": "FAIL" if failures else "PASS",
        "scope": "Local artifact checks only. Rebuild after source changes; this is not store or hardware approval.",
        "checks": checks, "failed_checks": failures,
        "upload_signature_verified": signed,
        "manual_release_gates": ["Owner-approved public privacy and support details",
                                 "Physical NFC and same-key update acceptance",
                                 "Real store screenshots and final content declarations",
                                 "Play internal/closed testing and production access",
                                 "Final owner review of account, track, certificate and build hash"],
    }
    rendered = json.dumps(report, indent=2, ensure_ascii=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
