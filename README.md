# Практичне завдання 4: кодування даних, RPC і черга повідомлень

Звіт з результатами: [REPORT.md](REPORT.md).

## Структура

```
schema/v1/shop.proto        схема v1
schema/v2/shop.proto        схема v2: додано promo_code (8), видалено comment (7, reserved)
schema/v2break/shop.proto   окрема несумісна зміна: OrderItem.quantity uint32 -> sint32
gen.sh                      генерація коду Python і JS з однієї схеми для кожної версії
gen_orders.py               генерація 10 000 тестових замовлень (seed 42) у data/orders.json
shop.py                     спільне для Python: вибір версії схеми, конвертація, опис повідомлень
order_service.py            сервіс замовлень (Python): gRPC сервер + публікація/споживання RabbitMQ
warehouse.py                сервіс складу (Python): споживає orders.created, публікує orders.results
client/client.js            клієнт (Node.js, gRPC)
client/bench_encoding.js    експеримент 1 для Node.js
client/reencode.js          експеримент 2: v1 у Node.js перекодовує повідомлення v2
experiments/                скрипти експериментів 1-4
results/                    сирі результати запусків
docker-compose.yml          RabbitMQ
```

## Підготовка

```bash
docker compose up -d                       # RabbitMQ 4.1, 5672 і веб-панель 15672 (guest/guest)
python3 -m venv .venv && .venv/bin/pip install grpcio==1.85.0 grpcio-tools==1.85.0 protobuf==7.36.2 pika==1.4.4
(cd client && npm install)
./gen.sh                                   # gen/python/<версія>, client/gen/<версія>
.venv/bin/python gen_orders.py             # data/orders.json
```

## Запуск з потрібною версією схеми

Кожен процес приймає `--schema v1|v2|v2break`, версії можна змішувати.

```bash
.venv/bin/python order_service.py --schema v2            # gRPC на 127.0.0.1:50051
.venv/bin/python warehouse.py --schema v1
node client/client.js --schema v1 create-one --index 1   # створити й прочитати одне замовлення
node client/client.js --schema v1 get <id>
node client/client.js --schema v1 list cust-00042
node client/client.js --schema v1 create-all --n 10000 --ids ids.txt
```

Додаткові параметри сервісу замовлень: `--delay-ms N` (затримка в CreateOrder), `--idempotent`
(дедуплікація за request_id), `--transient` (повідомлення без збереження на диск),
`--no-broker` (лише частина A), `--verbose`.
Сервісу складу: `--ack-mode after|batch|auto`, `--confirm` (publisher confirms для результатів),
`--prefetch`, `--work-ms`, `--verbose`.

## Експерименти

```bash
.venv/bin/python experiments/bench_encoding.py   # експеримент 1, Python
node client/bench_encoding.js                    # експеримент 1, Node.js
experiments/bench_rpc.sh [--with-broker]         # експеримент 1, час відповіді CreateOrder
.venv/bin/python experiments/hexdump_order.py    # hex-дамп для звіту
experiments/compat.sh                            # експеримент 2, матриця сумісності
experiments/failures_rpc.sh                      # експеримент 3
experiments/idempotency_restart.sh               # експеримент 3, перезапуск сервера між спробами
experiments/failures_queue.sh                    # експеримент 4
experiments/chaos_queue.sh after_confirm --ack-mode after --confirm   # 30 вбивств складу поспіль
experiments/broker_crash.sh                      # docker kill брокера з беклогом
```
