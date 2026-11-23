import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import public_guard as pg  # noqa: E402


def check(rel, text):
    return pg.check_file(rel, text.encode("utf-8"))


class PathRulesTest(unittest.TestCase):
    def test_blocked_types(self):
        for rel in ("a/com.syu.ms.apk", "boot.img", "x.tar.gz", "can_idle.log", "lib.so"):
            with self.subTest(rel=rel):
                self.assertTrue(pg.check_path(rel))

    def test_blocked_dirs(self):
        self.assertTrue(pg.check_path("dumps/build_props.txt"))
        self.assertTrue(pg.check_path("decompiled/a.java"))

    def test_smali_only_in_hooks(self):
        self.assertTrue(pg.check_path("patcher/Foo.smali"))
        self.assertFalse(pg.check_path("patcher/smali_hooks/org/openfyt/canbus/RawCanHook.smali"))

    def test_normal_files_pass(self):
        self.assertFalse(pg.check_path("protocols/renault/megane2_ph2_raise.json"))


class ContentRulesTest(unittest.TestCase):
    def test_vin(self):
        self.assertTrue(check("a.md", "VIN: WVWZZZ1KZAW000001"))  # public-guard: allow

    def test_not_vin(self):
        self.assertFalse(check("a.md", "ABCDEFGHJKLMNPRST no digits"))
        self.assertFalse(check("a.md", "12345678901234567 no letters"))

    def test_ip(self):
        self.assertTrue(check("a.md", "adb connect 192.168.1.50:5555"))  # public-guard: allow
        self.assertFalse(check("a.md", "adb connect 192.0.2.10:5555 або 127.0.0.1"))
        self.assertFalse(check("a.md", "версія 1.2.3"))

    def test_mac(self):
        self.assertTrue(check("a.txt", "wlan aa:bb:cc:dd:ee:ff"))  # public-guard: allow

    def test_serial_and_getprop(self):
        self.assertTrue(check("a.txt", "[ro.serialno]: [XYZ123]"))  # public-guard: allow
        dump = "\n".join(f"[ro.prop{i}]: [v]" for i in range(6))
        self.assertTrue(check("props.txt", dump))

    def test_syu_code(self):
        self.assertTrue(check("A.java", "package com.syu.module.canbus;"))
        self.assertTrue(check("patcher/smali_hooks/org/openfyt/X.smali", ".class public Lcom/syu/A;"))
        self.assertFalse(check("test.py", '".class public Lcom/syu/A;"'))

    def test_allow_mark(self):
        self.assertFalse(check("a.md", "192.168.1.1  # public-guard: allow"))

    def test_size_and_binary(self):
        self.assertTrue(pg.check_file("a.txt", b"x" * (pg.MAX_SIZE + 1)))
        self.assertTrue(pg.check_file("a.dat", b"\x00\x01"))


class RepoTest(unittest.TestCase):
    def test_current_repo_passes(self):
        self.assertEqual(pg.main(["--all", "--root", str(ROOT)]), 0)

    def test_staged_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            (repo / "ok.md").write_text("hello\n", encoding="utf-8")
            (repo / "bad.md").write_text("10.0.0.7\n", encoding="utf-8")  # public-guard: allow
            subprocess.run(["git", "-C", str(repo), "add", "ok.md"], check=True)
            self.assertEqual(pg.main(["--staged", "--root", str(repo)]), 0)
            subprocess.run(["git", "-C", str(repo), "add", "bad.md"], check=True)
            self.assertEqual(pg.main(["--staged", "--root", str(repo)]), 1)


if __name__ == "__main__":
    unittest.main()
