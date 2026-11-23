#!/usr/bin/env python3
"""Перевіряє файли перед потраплянням у публічний репозиторій can2din.

Блокує: пропрієтарні бінарні типи, дампи й декомпіляцію, файли > 1 МБ,
VIN, IP- та MAC-адреси, серійні номери й дампи getprop, код com.syu.
Знайдені значення не виводяться — лише файл, рядок і правило.

Режими:
  public_guard.py --staged            файли з індексу Git (для pre-commit)
  public_guard.py --all               усі файли під контролем Git
  public_guard.py --root DIR FILE...  вказані файли відносно DIR
Рядок із позначкою "public-guard: allow" пропускається.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

MAX_SIZE = 1024 * 1024
ALLOW_MARK = "public-guard: allow"

BLOCKED_SUFFIXES = (
    ".apk", ".dex", ".odex", ".vdex", ".oat", ".jar", ".so",
    ".img", ".bin", ".zip", ".tar.gz", ".tgz", ".log",
)
BLOCKED_DIRS = ("dumps", "decompiled", "work")
SMALI_ALLOWED_PREFIX = "patcher/smali_hooks/org/openfyt/"

VIN_RE = re.compile(r"\b(?=[A-HJ-NPR-Z0-9]*\d)(?=[A-HJ-NPR-Z0-9]*[A-HJ-NPR-Z])[A-HJ-NPR-Z0-9]{17}\b")
IPV4_RE = re.compile(r"(?<![\d.])((?:25[0-5]|2[0-4]\d|1?\d?\d)(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3})(?![\d.])")
IP_ALLOWED = re.compile(r"^(127\.0\.0\.1|0\.0\.0\.0|192\.0\.2\.\d+|198\.51\.100\.\d+|203\.0\.113\.\d+)$")
MAC_RE = re.compile(r"\b[0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5}\b")
SERIAL_RE = re.compile(r"\[ro\.(?:boot\.)?serialno\]\s*:\s*\[[^\]]+\]")
GETPROP_LINE_RE = re.compile(r"^\[[\w.\-]+\]: \[")
GETPROP_LIMIT = 5
SYU_JAVA_RE = re.compile(r"^\s*package\s+com\.syu\b")
SYU_SMALI_RE = re.compile(r"^\.class\b.*\bLcom/syu/")


def check_path(rel: str) -> list[str]:
    p = PurePosixPath(rel)
    errors = []
    name = p.name.lower()
    if any(name.endswith(s) for s in BLOCKED_SUFFIXES):
        errors.append("заборонений тип файлу")
    if p.parts and p.parts[0] in BLOCKED_DIRS:
        errors.append(f"тека {p.parts[0]}/ не публікується")
    if name.endswith(".smali") and not rel.startswith(SMALI_ALLOWED_PREFIX):
        errors.append(f".smali дозволено лише в {SMALI_ALLOWED_PREFIX}")
    return errors


def check_content(rel: str, data: bytes) -> list[str]:
    if len(data) > MAX_SIZE:
        return [f"розмір {len(data)} Б перевищує {MAX_SIZE} Б"]
    if b"\0" in data[:8192]:
        return ["двійковий файл"]
    text = data.decode("utf-8", errors="replace")
    suffix = PurePosixPath(rel).suffix.lower()
    errors = []
    getprop_lines = 0
    for no, line in enumerate(text.splitlines(), 1):
        if ALLOW_MARK in line:
            continue
        if VIN_RE.search(line):
            errors.append(f"рядок {no}: схоже на VIN")
        if any(not IP_ALLOWED.match(m.group(1)) for m in IPV4_RE.finditer(line)):
            errors.append(f"рядок {no}: IP-адреса")
        if MAC_RE.search(line):
            errors.append(f"рядок {no}: MAC-адреса")
        if SERIAL_RE.search(line):
            errors.append(f"рядок {no}: серійний номер пристрою")
        if GETPROP_LINE_RE.match(line):
            getprop_lines += 1
        if suffix in (".java", ".kt") and SYU_JAVA_RE.match(line):
            errors.append(f"рядок {no}: код пакета com.syu")
        if suffix == ".smali" and SYU_SMALI_RE.match(line):
            errors.append(f"рядок {no}: клас com.syu")
    if getprop_lines >= GETPROP_LIMIT:
        errors.append(f"схоже на дамп getprop ({getprop_lines} рядків)")
    return errors


def check_file(rel: str, data: bytes) -> list[str]:
    errors = check_path(rel)
    if not errors:
        errors = check_content(rel, data)
    return errors


def _git(root: Path, *args: str) -> bytes:
    return subprocess.run(["git", "-C", str(root), *args], check=True,
                          capture_output=True).stdout


def collect(args) -> list[tuple[str, bytes]]:
    root = args.root
    if args.staged:
        names = _git(root, "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z")
        rels = [n.decode() for n in names.split(b"\0") if n]
        return [(r, _git(root, "show", f":{r}")) for r in rels]
    if args.all:
        rels = [n.decode() for n in _git(root, "ls-files", "-z").split(b"\0") if n]
    else:
        rels = [PurePosixPath(Path(f).as_posix()).as_posix() for f in args.files]
    return [(r, (root / r).read_bytes()) for r in rels]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Перевірка файлів перед публікацією в can2din")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--staged", action="store_true")
    mode.add_argument("--all", action="store_true")
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("files", nargs="*")
    args = ap.parse_args(argv)
    if not (args.staged or args.all or args.files):
        ap.error("вкажіть --staged, --all або файли")

    failed = 0
    for rel, data in collect(args):
        for err in check_file(rel, data):
            print(f"{rel}: {err}", file=sys.stderr)
            failed += 1
    if failed:
        print(f"public_guard: знайдено проблем: {failed}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
