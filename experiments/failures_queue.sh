#!/usr/bin/env bash
# Експеримент 4: збої під час обміну через чергу, 10 000 повідомлень.
cd "$(dirname "$0")/.."
PY=.venv/bin/python
OUT=${OUT:-logs/exp4}
rm -rf "$OUT"; mkdir -p "$OUT"

qstat() {
  docker exec shop-rabbitmq rabbitmqctl list_queues -q name messages_ready messages_unacknowledged 2>/dev/null \
    | awk '$1=="orders.created"{printf "ready=%s unacked=%s", $2, $3}'
}

purge() {
  for q in orders.created orders.results; do docker exec shop-rabbitmq rabbitmqctl purge_queue "$q" >/dev/null 2>&1; done
}

wait_drained() {  # чекає, поки черга порожня і склад перестав писати в лог
  local f=$1 prev=-1 cur
  for _ in $(seq 1 120); do
    sleep 2
    cur=$(wc -l < "$f" 2>/dev/null || echo 0)
    if [ "$cur" = "$prev" ] && qstat | grep -q "ready=0 unacked=0"; then return; fi
    prev=$cur
  done
}

prepare() {  # $1 каталог: сервіс замовлень публікує 10 000 замовлень, поки склад зупинений
  purge
  $PY order_service.py --schema v1 --port 50091 --log-dir "$1/orders" > "$1/orders.log" 2>&1 &
  OS=$!
  sleep 1.5
  node client/client.js --schema v1 --addr 127.0.0.1:50091 create-all --n 10000 --ids "$1/ids.txt" > /dev/null
  sleep 1
  echo "  склад зупинений, у черзі orders.created: $(qstat)"
}

finish() {  # $1 каталог
  wait_drained "$1/warehouse/processed.log"
  sleep 2
  echo "  стани замовлень у сервісі: $(node client/client.js --schema v1 --addr 127.0.0.1:50091 wait-status --ids "$1/ids.txt" --timeout 5)"
  kill $WH $OS 2>/dev/null; wait $WH $OS 2>/dev/null
  $PY experiments/analyze_queue.py "$1/ids.txt" "$1/warehouse/processed.log" "$1/orders/results.log" | sed 's/^/  /'
}

if [ -z "$SKIP_A" ]; then
echo "=== 4a: склад зупинений, 10 000 повідомлень, потім запуск складу (ack після обробки)"
D=$OUT/a; mkdir -p "$D"
prepare "$D"
$PY warehouse.py --schema v1 --ack-mode after --log-dir "$D/warehouse" > "$D/wh.log" 2>&1 &
WH=$!
finish "$D"
fi

for mode in ${MODES:-after batch auto}; do
  echo "=== 4b: kill -9 складу посеред обробки, ack-mode=$mode"
  D=$OUT/b_$mode; mkdir -p "$D"
  prepare "$D"
  $PY warehouse.py --schema v1 --ack-mode $mode --log-dir "$D/warehouse" > "$D/wh1.log" 2>&1 &
  WH=$!
  sleep 3
  kill -9 $WH; wait $WH 2>/dev/null
  echo "  після kill -9: оброблено рядків $(wc -l < "$D/warehouse/processed.log"), черга: $(qstat)"
  sleep 1
  echo "  через 1 с після kill: $(qstat)"
  $PY warehouse.py --schema v1 --ack-mode $mode --log-dir "$D/warehouse" > "$D/wh2.log" 2>&1 &
  WH=$!
  finish "$D"
done
purge
