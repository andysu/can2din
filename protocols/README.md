# Профілі авто

Один JSON-файл на комбінацію авто + Canbox: `protocols/<марка>/<модель>_<canbox>.json`. Формат описано в [schema.json](schema.json).

- `status`: `draft` — каркас без перевірених даних, `partial` — частина фреймів підтверджена, `verified` — профіль перевірено на авто.
- `cmd_type` — байт `cmdType` з UART-пакета ([docs/UART_PROTOCOL.md](../docs/UART_PROTOCOL.md)) у вигляді `0xNN`.
- `update_code` — відповідний код з [docs/UPDATE_CODES.md](../docs/UPDATE_CODES.md), якщо він є.

Не додавайте до профілів VIN, номери або інші дані, що ідентифікують конкретне авто чи власника.

Перевірка: `python3 -m unittest tests.test_profiles`.
