# smali_hooks

Власні smali-класи у просторі імен `org/openfyt/canbus/`. `inject_patch.py` копіює всі `*.smali` звідси в `smali/` розпакованого APK.

Очікуваний клас — `org/openfyt/canbus/RawCanHook.smali` зі статичним методом `onFrame([B)V`: трансляція сирого фрейму в Broadcast Intent і застосування JSON-правил з `protocols/`. Клас ще не написаний (етап 3 у TODO.md): спершу треба визначити в JADX, який метод callback-класу отримує фрейм і в якому регістрі.

Поки файлу немає, `inject_patch.py` відмовляється патчити APK (крім режиму `--allow-missing-hook`).
