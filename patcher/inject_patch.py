#!/usr/bin/env python3
"""Вставляє виклик хука can2din у локально розпаковану (apktool) копію com.syu.ms.apk.

Скрипт змінює рівно один метод: на початку його тіла додається
    invoke-static/range {<reg> .. <reg>}, Lorg/openfyt/canbus/RawCanHook;->onFrame([B)V
і копіює smali-хуки з patcher/smali_hooks/ у дерево APK.
Повторний запуск нічого не змінює (маркер MARKER).
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

MARKER = "# can2din-hook"
HOOK_CLASS = "Lorg/openfyt/canbus/RawCanHook;"
HOOK_METHOD = "onFrame([B)V"
HOOK_REL_PATH = Path("org/openfyt/canbus/RawCanHook.smali")
DEFAULT_HOOKS_DIR = Path(__file__).resolve().parent / "smali_hooks"

REGISTER_RE = re.compile(r"^[pv]\d+$")


class PatchError(Exception):
    pass


def find_class_file(smali_root: Path, class_path: str) -> Path:
    rel = Path(class_path.strip("/").removesuffix(".smali") + ".smali")
    candidates = sorted(smali_root.glob("smali*/" + rel.as_posix()))
    if not candidates:
        raise PatchError(f"клас {class_path} не знайдено в {smali_root}/smali*/")
    if len(candidates) > 1:
        raise PatchError(f"клас {class_path} знайдено кілька разів: {candidates}")
    return candidates[0]


def _find_method_start(lines: list[str], method: str) -> int:
    matches = [
        i for i, line in enumerate(lines)
        if line.startswith(".method ") and line.rstrip().endswith(" " + method)
    ]
    if not matches:
        raise PatchError(f"метод {method} не знайдено")
    if len(matches) > 1:
        raise PatchError(f"метод {method} знайдено кілька разів")
    return matches[0]


def _find_insert_index(lines: list[str], start: int) -> int:
    """Індекс першого рядка коду після .locals/.registers, .param і .annotation."""
    i = start + 1
    seen_locals = False
    block_end = None
    while i < len(lines):
        s = lines[i].strip()
        if s == ".end method":
            raise PatchError("метод без тіла (abstract/native?)")
        if block_end:
            if s == block_end:
                block_end = None
            i += 1
            continue
        if s.startswith((".locals", ".registers")):
            seen_locals = True
        elif s.startswith((".param", ".end param")):
            # блок .param ... .end param містить лише .annotation, які пропускаються нижче
            pass
        elif s.startswith(".annotation"):
            block_end = ".end annotation"
        elif s and s != ".prologue" and not s.startswith("#"):
            if not seen_locals:
                raise PatchError("не знайдено .locals/.registers перед кодом методу")
            return i
        i += 1
    raise PatchError("не знайдено кінець методу")


def patch_lines(lines: list[str], method: str, register: str) -> tuple[list[str], bool]:
    """Повертає (нові рядки, чи були зміни)."""
    if not REGISTER_RE.match(register):
        raise PatchError(f"некоректний регістр: {register}")
    start = _find_method_start(lines, method)
    end = next(i for i in range(start, len(lines)) if lines[i].strip() == ".end method")
    if any(MARKER in line for line in lines[start:end]):
        return lines, False
    idx = _find_insert_index(lines, start)
    hook = [
        f"    {MARKER}\n",
        f"    invoke-static/range {{{register} .. {register}}}, {HOOK_CLASS}->{HOOK_METHOD}\n",
        "\n",
    ]
    return lines[:idx] + hook + lines[idx:], True


def copy_hooks(hooks_dir: Path, smali_root: Path) -> list[Path]:
    target_root = smali_root / "smali"
    copied = []
    for src in sorted(hooks_dir.rglob("*.smali")):
        dst = target_root / src.relative_to(hooks_dir)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied.append(dst)
    return copied


def run(smali_root: Path, class_path: str, method: str, register: str,
        hooks_dir: Path, allow_missing_hook: bool, dry_run: bool) -> bool:
    if not (smali_root / "apktool.yml").is_file():
        raise PatchError(f"{smali_root} не схоже на теку apktool (немає apktool.yml)")
    if not (hooks_dir / HOOK_REL_PATH).is_file() and not allow_missing_hook:
        raise PatchError(
            f"немає {hooks_dir / HOOK_REL_PATH}; без хука APK впаде з NoClassDefFoundError. "
            "Для перевірки самої вставки використайте --allow-missing-hook"
        )
    target = find_class_file(smali_root, class_path)
    lines = target.read_text(encoding="utf-8").splitlines(keepends=True)
    new_lines, changed = patch_lines(lines, method, register)
    if not changed:
        print(f"{target}: хук уже вставлено, змін немає")
        return False
    if dry_run:
        print(f"{target}: буде вставлено хук у {method} (dry-run, файли не змінено)")
        return True
    target.write_text("".join(new_lines), encoding="utf-8")
    print(f"{target}: хук вставлено в {method}")
    for path in copy_hooks(hooks_dir, smali_root):
        print(f"скопійовано {path}")
    return True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("smali_root", type=Path, help="тека, створена 'apktool d'")
    ap.add_argument("--class", dest="class_path", required=True,
                    help="клас у форматі com/syu/module/canbus/Callback_XXXX")
    ap.add_argument("--method", required=True,
                    help="ім'я методу з сигнатурою, напр. 'cmd(I[BI)V'")
    ap.add_argument("--register", required=True,
                    help="регістр з byte[] фрейму, напр. p2")
    ap.add_argument("--hooks-dir", type=Path, default=DEFAULT_HOOKS_DIR)
    ap.add_argument("--allow-missing-hook", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    try:
        run(args.smali_root, args.class_path, args.method, args.register,
            args.hooks_dir, args.allow_missing_hook, args.dry_run)
    except PatchError as exc:
        print(f"помилка: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
