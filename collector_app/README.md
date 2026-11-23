# FYT Canbus Collector (заплановано)

Android-додаток на Kotlin для збору даних без ПК (етап 4 у [TODO.md](../TODO.md)):

- збір `build_props`, `fyt.prop`, копії `com.syu.ms.apk`;
- підключення до `com.syu.ipc.IRemoteToolkit` та `logcat`;
- маркери дій користувача (`VOL_UP`, `DOOR_FL` тощо) під час запису;
- ручний вибір авто (марка / модель / рік / Canbox), опціонально VIN;
- пакування в ZIP для надсилання.

Код ще не створено. Цільова платформа — Android 10 (API 29) на FYT UIS7862.
