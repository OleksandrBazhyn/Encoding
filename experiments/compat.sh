#!/usr/bin/env bash
# Експеримент 2: усі комбінації версій схеми для виклику (частина A) і черги (частина B).
# Замовлення №1 з data/orders.json має і comment, і promo_code, item0.quantity=5.
cd "$(dirname "$0")/.."
PY=.venv/bin/python
OUT=logs/compat
rm -rf "$OUT"; mkdir -p "$OUT"

purge() {
  for q in orders.created orders.results; do docker exec shop-rabbitmq rabbitmqctl purge_queue "$q" >/dev/null 2>&1; done
}

rpc_case() {  # $1 клієнт, $2 сервер
  echo "=== RPC: клієнт $1 -> сервер $2"
  $PY order_service.py --schema "$2" --port 50071 --no-broker --verbose --log-dir "$OUT/tmp" > "$OUT/srv.log" 2>&1 &
  local pid=$!
  sleep 1.2
  node client/client.js --schema "$1" --addr 127.0.0.1:50071 create-one --index 1 2>&1 | sed 's/^/  клієнт  /'
  kill $pid; wait $pid 2>/dev/null
  grep -o "CreateOrder отримано.*" "$OUT/srv.log" | sed 's/^/  сервер  /'
}

queue_case() {  # $1 сервіс замовлень (відправник), $2 склад (отримувач)
  echo "=== Черга: сервіс замовлень $1 -> склад $2"
  purge
  $PY order_service.py --schema "$1" --port 50072 --verbose --log-dir "$OUT/tmp" > "$OUT/os.log" 2>&1 &
  local os=$!
  $PY warehouse.py --schema "$2" --verbose --log-dir "$OUT/tmp" > "$OUT/wh.log" 2>&1 &
  local wh=$!
  sleep 1.5
  node client/client.js --schema "$1" --addr 127.0.0.1:50072 create-one --index 1 > /dev/null
  sleep 1
  kill $os $wh; wait $os $wh 2>/dev/null
  grep -oE "(отримано|не вдалося).*" "$OUT/wh.log" | sed 's/^/  склад отримав    /'
  grep -o "результат.*" "$OUT/os.log" | sed 's/^/  сервіс замовлень /'
}

backlog_case() {  # $1 версія повідомлень у черзі, $2 версія перезапущеного складу
  echo "=== Черга: 5 повідомлень $1 накопичились, склад перезапущено з $2"
  purge
  $PY order_service.py --schema "$1" --port 50073 --verbose --log-dir "$OUT/tmp" > "$OUT/os.log" 2>&1 &
  local os=$!
  sleep 1.5
  for i in 1 2 3 4 5; do node client/client.js --schema "$1" --addr 127.0.0.1:50073 create-one --index $i > /dev/null; done
  echo "  у черзі: $(docker exec shop-rabbitmq rabbitmqctl list_queues -q name messages 2>/dev/null | grep created)"
  $PY warehouse.py --schema "$2" --verbose --log-dir "$OUT/tmp" > "$OUT/wh.log" 2>&1 &
  local wh=$!
  sleep 2
  kill $os $wh; wait $os $wh 2>/dev/null
  grep -oE "(отримано|не вдалося).*" "$OUT/wh.log" | sed 's/^/  склад отримав    /'
  grep -o "результат.*" "$OUT/os.log" | sed 's/^/  сервіс замовлень /'
}

echo "##### Сумісні зміни (v1 <-> v2)"
rpc_case v1 v1
rpc_case v1 v2
rpc_case v2 v1
queue_case v2 v1
backlog_case v1 v2
echo
echo "##### Несумісна зміна (v1 <-> v2break, quantity uint32 -> sint32)"
rpc_case v1 v2break
rpc_case v2break v1
queue_case v1 v2break
queue_case v2break v1
purge
