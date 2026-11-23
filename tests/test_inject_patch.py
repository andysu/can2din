import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "patcher"))

import inject_patch as ip  # noqa: E402

SAMPLE = """\
.class public Lcom/syu/module/canbus/Callback_TEST;
.super Ljava/lang/Object;

.method public cmd(I[BI)V
    .locals 2
    .param p1, "type"    # I
    .param p2, "data"    # [B
    .annotation runtime Ljava/lang/Deprecated;
    .end annotation

    .line 10
    const/4 v0, 0x0
    return-void
.end method

.method public other()V
    .locals 0
    return-void
.end method
"""


def lines(text):
    return text.splitlines(keepends=True)


class PatchLinesTest(unittest.TestCase):
    def test_inserts_after_directives(self):
        out, changed = ip.patch_lines(lines(SAMPLE), "cmd(I[BI)V", "p2")
        self.assertTrue(changed)
        text = "".join(out)
        hook = "invoke-static/range {p2 .. p2}, Lorg/openfyt/canbus/RawCanHook;->onFrame([B)V"
        self.assertIn(hook, text)
        self.assertLess(text.index(".end annotation"), text.index(hook))
        self.assertLess(text.index(hook), text.index(".line 10"))
        self.assertEqual(text.count(hook), 1)

    def test_idempotent(self):
        once, _ = ip.patch_lines(lines(SAMPLE), "cmd(I[BI)V", "p2")
        twice, changed = ip.patch_lines(once, "cmd(I[BI)V", "p2")
        self.assertFalse(changed)
        self.assertEqual(once, twice)

    def test_other_method_untouched(self):
        out, _ = ip.patch_lines(lines(SAMPLE), "other()V", "p0")
        text = "".join(out)
        self.assertEqual(text.count(ip.MARKER), 1)
        self.assertGreater(text.index(ip.MARKER), text.index(".method public other()V"))

    def test_missing_method(self):
        with self.assertRaises(ip.PatchError):
            ip.patch_lines(lines(SAMPLE), "nope()V", "p1")

    def test_bad_register(self):
        with self.assertRaises(ip.PatchError):
            ip.patch_lines(lines(SAMPLE), "cmd(I[BI)V", "p2; nop")

    def test_abstract_method(self):
        src = ".method public abstract a()V\n.end method\n"
        with self.assertRaises(ip.PatchError):
            ip.patch_lines(lines(src), "a()V", "p0")


class RunTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.apk = root / "ms_src"
        cls = self.apk / "smali_classes2/com/syu/module/canbus/Callback_TEST.smali"
        cls.parent.mkdir(parents=True)
        cls.write_text(SAMPLE, encoding="utf-8")
        (self.apk / "apktool.yml").write_text("version: test\n", encoding="utf-8")
        self.cls = cls
        self.hooks = root / "hooks"
        self.hook_file = self.hooks / ip.HOOK_REL_PATH

    def tearDown(self):
        self.tmp.cleanup()

    def call(self, **kw):
        args = dict(smali_root=self.apk, class_path="com/syu/module/canbus/Callback_TEST",
                    method="cmd(I[BI)V", register="p2", hooks_dir=self.hooks,
                    allow_missing_hook=False, dry_run=False)
        args.update(kw)
        return ip.run(**args)

    def test_refuses_without_hook(self):
        with self.assertRaises(ip.PatchError):
            self.call()
        self.assertEqual(self.cls.read_text(encoding="utf-8"), SAMPLE)

    def test_patches_and_copies_hook(self):
        self.hook_file.parent.mkdir(parents=True)
        self.hook_file.write_text(".class public Lorg/openfyt/canbus/RawCanHook;\n", encoding="utf-8")
        self.assertTrue(self.call())
        self.assertIn(ip.MARKER, self.cls.read_text(encoding="utf-8"))
        self.assertTrue((self.apk / "smali" / ip.HOOK_REL_PATH).is_file())
        self.assertFalse(self.call())

    def test_dry_run_keeps_file(self):
        self.assertTrue(self.call(allow_missing_hook=True, dry_run=True))
        self.assertEqual(self.cls.read_text(encoding="utf-8"), SAMPLE)

    def test_requires_apktool_dir(self):
        (self.apk / "apktool.yml").unlink()
        with self.assertRaises(ip.PatchError):
            self.call(allow_missing_hook=True)


if __name__ == "__main__":
    unittest.main()
