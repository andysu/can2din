# Обробка CAN-даних у прошивці FYT

Опис складено за попереднім аналізом; назви класів для Renault Raise ще треба підтвердити в JADX (етап 3 у TODO).

## Ланцюжок

```text
CAN-шина → Canbox (Raise) → UART → MCU → com.syu.ms → updateCode → com.syu.canbus / лаунчер
```

1. `190000000_com.syu.ms.apk` (Main Server, `/oem/app/`):
   - приймає UART-пакети від MCU (формат — [UART_PROTOCOL.md](UART_PROTOCOL.md));
   - розбирає їх у класах `com.syu.module.canbus.Callback_XXXX_RZC_...`; для Renault Raise імовірно `Callback_0145_RZC_XP1_Renault` або суміжний клас із `ModuleCallbackList.java`;
   - передає значення через `HandlerCanbus.update(updateCode, value)` у масив `DataCanbus.DATA[]` та через AIDL-інтерфейс `com.syu.ipc.IRemoteToolkit`.
2. `190000001_com.syu.canbus.apk` і лаунчер Teyes підписуються на `updateCode` з `com.syu.ms` і показують дані в UI та 3D-віджеті авто.

## Точки втручання

- **Хук на вході callback-класу.** `patcher/inject_patch.py` вставляє на початку методу розбору виклик `org.openfyt.canbus.RawCanHook.onFrame([B)V`. Хук транслює сирий фрейм у Broadcast Intent і може застосовувати зовнішні JSON-правила з `protocols/`. Зміна в пропрієтарному APK — один рядок, решта коду в окремому просторі імен.
- **AIDL `IRemoteToolkit`.** Сторонній додаток (collector_app) може підписатися на вже розібрані `updateCode` без патчу.
- **logcat.** При увімкненому CAN Log (`3368` → Print Canbus Data) сирі дані видно в журналі.

## Обмеження

- Публікувати код або APK FYT/Teyes не можна; патч застосовується користувачем локально до власної копії.
- Без вимкненої перевірки підписів (як у збірці `gordgelin`) перепідписаний системний APK не встановиться.
