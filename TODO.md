# TODO

Джерело плану — хендофф від 2026-11-22 (локальний, не в Git: містить VIN).

## Етап 0: Каркас публічного репозиторію
- [x] Структура репозиторію, документація, схема профілів, патчер з тестами, скрипт дампу (2026-11-23)

## Етап 0.1: Приватний репозиторій і ручна публікація (погоджено 2026-11-23)
Два окремі репо поруч: `~/can2din` (публічний) і `~/can2din_private` (приватний, `andysu/can2din_private`). У публічний потрапляють лише файли з маніфесту після перевірок; запуск вручну.
- [ ] Структура `can2din_private` (README, TODO, `.gitignore`, `dumps/`, `analysis/`, `tools/`, `publish/`), перенести хендофф
- [ ] `publish/publish.py` + `manifest.json` + unit-тести (заборонені типи, VIN/IP/MAC/serial, розмір, білий список, dry-run, `--push`)
- [ ] `tools/public_guard.py` + pre-commit hook у публічному репо (`tools/install_hooks.sh`)
- [ ] Розділити TODO: дослідницькі роботи (етапи 1–2, аналіз етапу 3) — у приватний
- [ ] README обох репо: схема пари репозиторіїв і порядок публікації
- [ ] Перевірка: тести обох репо, dry-run публікації чорнового профілю; commit і push обох

## Етап 1: Повний бекап та технічний дамп
- [ ] Бекап збірки `gordgelin` поза Git: `boot.img`, `super.img` через `dd` з `/dev/block/by-name/`
- [ ] Зберегти `/oem/app/config.txt` та архів `/oem` (`oem_backup.tar.gz`)
- [ ] Дамп робочих файлів (`tools/adb_dump.sh`): `build_props.txt`, `fyt.prop`, `com.syu.ms.apk`, `com.syu.canbus.apk`
- [ ] Перевірити `rw`-доступ до `/oem`: `su -c 'mount -o rw,remount /oem'`

## Етап 2: Апаратна перевірка та CAN-логи з Megane 2
- [ ] На вимкненому запалюванні підключити штатний верхній дисплей
- [ ] Перевірити зовнішню температуру на верхньому екрані та у віджеті Teyes
- [ ] У заводських налаштуваннях (`3368`) увімкнути CAN Log / Print Canbus Data
- [ ] Записати `can_idle.log` (15–20 с у спокої)
- [ ] Записати `can_actions.log` (джойстик, габарити, задній хід, двері)

## Етап 3: Аналіз у JADX та Smali-хук
- [ ] Декомпілювати `com.syu.ms.apk` у JADX-GUI
- [ ] Знайти `Callback_XXXX` для Renault Raise у `ModuleCallbackList.java`, звірити оброблені й проігноровані байти з логами
- [ ] Уточнити `docs/UART_PROTOCOL.md` (контрольна сума) і заповнити `docs/UPDATE_CODES.md`
- [ ] Заповнити `protocols/renault/megane2_ph2_raise.json` реальними фреймами
- [ ] Написати `org.openfyt.canbus.RawCanHook` (сирі фрейми → Broadcast Intent, читання JSON-правил)
- [ ] Визначити цільовий клас/метод для `inject_patch.py` і перевірити патч на пристрої

## Етап 4: APK-збирач «FYT Canbus Collector»
- [ ] Kotlin-додаток: збір `build_props`, `fyt.prop`, копії `com.syu.ms.apk`, підключення до `IRemoteToolkit` / `logcat`
- [ ] Маркери дій користувача (`VOL_UP`, `DOOR_FL` тощо) і пакування в ZIP
- [ ] Ручний вибір авто (марка / модель / рік / Canbox) + опціональний VIN
