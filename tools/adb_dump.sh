#!/usr/bin/env bash
# Збирає технічний дамп з ГП FYT через ADB (етап 1 у TODO.md).
# Використання: tools/adb_dump.sh [тека_виводу]   (за замовчуванням ./work/dump)
# Пристрій має бути підключений: adb connect <IP>:5555
# Скрипт лише читає з пристрою; образи boot/super знімаються окремо вручну.
set -euo pipefail

out="${1:-./work/dump}"
mkdir -p "$out"

adb get-state >/dev/null

echo "== збірка"
adb shell "getprop ro.build.fytmanufacturer; getprop ro.build.display.id"

adb shell getprop > "$out/build_props.txt"
echo "getprop -> $out/build_props.txt"

for f in /oem/app/fyt.prop /oem/app/config.txt; do
    if adb pull "$f" "$out/" >/dev/null 2>&1; then
        echo "$f -> $out/"
    else
        echo "попередження: не вдалося скопіювати $f" >&2
    fi
done

for pkg in com.syu.ms com.syu.canbus; do
    path="$(adb shell pm path "$pkg" | head -n1 | cut -d: -f2 | tr -d '\r')"
    if [[ -z "$path" ]]; then
        echo "попередження: пакет $pkg не знайдено" >&2
        continue
    fi
    adb pull "$path" "$out/$pkg.apk" >/dev/null
    echo "$pkg ($path) -> $out/$pkg.apk"
done

echo "== перевірка rw для /oem (потрібен root)"
if adb shell "su -c 'mount -o rw,remount /oem && mount -o ro,remount /oem'" >/dev/null 2>&1; then
    echo "/oem: перемонтування в rw працює (повернено в ro)"
else
    echo "/oem: перемонтувати не вдалося (немає root або розділ зайнятий)" >&2
fi

echo "Готово. Тека $out не потрапляє в Git."
