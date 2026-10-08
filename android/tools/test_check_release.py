"""Regression checks for archive/signature guards; never uses a private key."""
import tempfile
import zipfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
import check_release


class ReleaseChecksTest(unittest.TestCase):
    def test_unsigned_jarsigner_zero_exit_is_not_a_verified_signature(self):
        with patch("check_release.shutil.which", return_value="jdk-tool"), patch(
                "check_release.subprocess.run", return_value=SimpleNamespace(returncode=0, stdout="jar is unsigned.")):
            self.assertFalse(check_release.verified_signature(Path("fixture.aab"), "AB" * 32))

    def test_verification_must_match_the_independently_recorded_certificate(self):
        results = [SimpleNamespace(returncode=0, stdout="jar verified."),
                   SimpleNamespace(returncode=0, stdout="SHA256: " + ":".join(["AB"] * 32))]
        with patch("check_release.shutil.which", return_value="jdk-tool"), patch(
                "check_release.subprocess.run", side_effect=results):
            self.assertFalse(check_release.verified_signature(Path("fixture.aab"), "CD" * 32))
        with patch("check_release.shutil.which", return_value="jdk-tool"), patch(
                "check_release.subprocess.run", side_effect=results):
            self.assertTrue(check_release.verified_signature(Path("fixture.aab"), "AB" * 32))

    def test_fingerprint_rejects_other_hash_lengths(self):
        with self.assertRaises(ValueError):
            check_release.normalize_fingerprint("AB" * 20)
        self.assertEqual("AB" * 32, check_release.normalize_fingerprint(":".join(["ab"] * 32)))

    def test_truncated_image_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "broken.png"
            image.write_bytes(b"\x89PNG\r\n\x1a\n")
            with self.assertRaises(ValueError):
                check_release.png_info(image)

    def test_an_empty_zip_cannot_pass_as_a_bundle(self):
        with tempfile.TemporaryDirectory() as directory:
            bundle = Path(directory) / "empty.aab"
            with zipfile.ZipFile(bundle, "w"):
                pass
            with self.assertRaises(ValueError):
                check_release.archive_info(bundle)


if __name__ == "__main__":
    unittest.main()
