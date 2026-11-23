# can2din

Відкритий набір інструментів для CAN-модуля головних пристроїв FYT на платформі UIS7862 (UMS512, Android 10).

Мета — отримувати з автомобіля більше даних, ніж показує штатна прошивка (зовнішня температура, події шини), і дати власникам інших авто спосіб додавати власні протоколи Canbox без перезбирання системної прошивки.

Стан: ранній етап. Протокол і коди оновлень ще не звірені з реальними логами. Поточний план — у [TODO.md](TODO.md).

## Що є в репозиторії

| Шлях | Призначення |
|---|---|
| [docs/HARDWARE_MEGANE2.md](docs/HARDWARE_MEGANE2.md) | Тестовий стенд: Renault Megane II Ph2 + Canbox Raise (RZC) + ГП FYT UIS7862 |
| [docs/FYT_ARCHITECTURE.md](docs/FYT_ARCHITECTURE.md) | Як прошивка FYT обробляє CAN-дані і де можна втрутитися |
| [docs/UART_PROTOCOL.md](docs/UART_PROTOCOL.md) | Формат пакетів MCU ↔ FYT |
| [docs/UPDATE_CODES.md](docs/UPDATE_CODES.md) | Таблиця внутрішніх `updateCode` (заповнюється) |
| [protocols/](protocols/) | JSON-профілі авто; схема — `protocols/schema.json` |
| [patcher/](patcher/) | `inject_patch.py` — вставляє виклик хука в локально розпакований `com.syu.ms.apk` |
| [tools/adb_dump.sh](tools/adb_dump.sh) | Збір технічного дампу з ГП через ADB |
| [tools/public_guard.py](tools/public_guard.py) | Перевірка файлів перед комітом і публікацією |
| [collector_app/](collector_app/) | Майбутній Android-додаток для збору профілів і CAN-логів |
| [tests/](tests/) | Unit-тести патчера та перевірка профілів |

## Що сюди не потрапляє

Код FYT/Teyes є пропрієтарним, тому в репозиторії немає APK, декомпільованих джерел, образів прошивок і сирих логів (див. `.gitignore`). Патчер працює лише з копією APK, яку користувач сам витягнув зі свого пристрою.

Дампи, логи й аналіз автор веде в окремому приватному репозиторії. Звідти сюди вручну публікуються лише перелічені файли: профілі авто і `docs/UPDATE_CODES.md`. Ці файли не варто правити тут напряму, наступна публікація їх перезапише. Перед кожною публікацією файли перевіряє `tools/public_guard.py`.

### Перевірка перед комітом

```bash
tools/install_hooks.sh
```

Скрипт підключає pre-commit hook. Hook запускає `tools/public_guard.py --staged` і блокує коміт, якщо знаходить APK, образи, логи, дампи getprop, код `com.syu`, VIN, IP/MAC-адреси або файли більші за 1 МБ. Хибне спрацювання на окремому рядку можна вимкнути позначкою `public-guard: allow`.

## Швидкий старт

Потрібні `adb` і ГП з увімкненим ADB (USB або Wi-Fi).

```bash
adb connect <IP_магнітоли>:5555
./tools/adb_dump.sh ./work/dump
```

Скрипт збирає `getprop`, `fyt.prop`, `config.txt` і копії `com.syu.ms.apk` / `com.syu.canbus.apk` у вказану теку. Тека `work/` ігнорується Git.

### Патчер

```bash
apktool d work/dump/com.syu.ms.apk -o work/ms_src
python3 patcher/inject_patch.py work/ms_src \
    --class com/syu/module/canbus/<Клас> \
    --method '<метод з сигнатурою>' \
    --register p1
```

Скрипт додає виклик `org.openfyt.canbus.RawCanHook.onFrame([B)V` на початку вказаного методу і копіює хуки з `patcher/smali_hooks/`. Цільовий клас і метод для Renault Raise ще не визначені (етап 3 у TODO). Після патчу APK треба зібрати (`apktool b`) і підписати.

## Тести

```bash
python3 -m unittest discover -s tests -v
```

## Ліцензія

MIT, див. [LICENSE](LICENSE).
