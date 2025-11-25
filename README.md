# ethscan-tokens-parser

Небольшой скрипт для вытягивания списка токенов с Etherscan и их цены в USD.

## Что делает

- Берёт HTML-страницу с токенами (по умолчанию `https://etherscan.io/tokens`).
- Находит записи о токенах и пытается вытащить:
  - имя/тикер токена,
  - цену в долларах США (float),
  - ссылку на страницу токена.
- Сортирует результат по убыванию цены.
- Сохраняет всё в JSON-файл.

## Установка

```bash
pip install -r requirements.txt
```

## Запуск

Базовый вариант:

```bash
python parse_crypto_v2.py
```

Опции:

- `-s, --source` — URL или путь к локальному HTML-файлу.  
  По умолчанию: `https://etherscan.io/tokens`.
- `-n, --limit` — максимальное число объектов в выводе (по умолчанию 1000).
- `-o, --out` — имя/путь выходного JSON-файла (по умолчанию `tokens.json`).

Пример:

```bash
# взять данные прямо с Etherscan, оставить только 50 токенов и сохранить в my_tokens.json
python parse_crypto_v2.py -s https://etherscan.io/tokens -n 50 -o my_tokens.json
```

## Формат результата

На выходе получается JSON-массив словарей:

```json
[
  {
    "name": "Wrapped BTC (WBTC)",
    "price_usd": 86333.0,
    "url": "https://etherscan.io/token/0x..."
  },
  {
    "name": "USDT",
    "price_usd": 1.0,
    "url": "https://etherscan.io/token/0x..."
  }
]
```
