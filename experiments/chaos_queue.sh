#!/usr/bin/env bash
# Експеримент 4, жорсткіший варіант: 10 000 повідомлень у черзі, склад вбивають kill -9
# KILLS разів у випадкові моменти, потім дають дообробити.
# Використання: experiments/chaos_queue.sh <назва> [аргументи warehouse.py]
cd "$(dirname "$0")/.."
PY=.venv/bin/python
NAME=$1; shift
KILLS=${KILLS:-30}
D=logs/chaos/$NAME
rm -rf "$D"; mkdir -p "$D"
RANDOM=7

for q in orders.created orders.results; do docker exec shop-rabbitmq rabbitmqctl purge_queue "$q" >/dev/null 2>&1; done
$PY order_service.py --schema v1 --port 50095 --log-dir "$D/orders" > "$D/orders.log" 2>&1 &
OS=$!
sleep 1.5
node client/client.js --schema v1 --addr 127.0.0.1:50095 create-all --n 10000 --ids "$D/ids.txt" > /dev/null

for i in $(seq 1 "$KILLS"); do
  $PY warehouse.py --schema v1 --log-dir "$D/warehouse" "$@" >> "$D/wh.log" 2>&1 &
  WH=$!
  # старт процесу і підключення займають близько 0.3 с, далі випадкові 0-0.4 с обробки
  sleep "0.3$((RANDOM % 10))"
  sleep "0.$((RANDOM % 4))$((RANDOM % 10))"
  kill -9 $WH; wait $WH 2>/dev/null
done
echo "  після $KILLS вбивств оброблено рядків: $(wc -l < "$D/warehouse/processed.log")"

$PY warehouse.py --schema v1 --log-dir "$D/warehouse" "$@" >> "$D/wh.log" 2>&1 &
WH=$!
prev=-1
for _ in $(seq 1 120); do
  sleep 2
  cur=$(wc -l < "$D/warehouse/processed.log")
  ready=$(docker exec shop-rabbitmq rabbitmqctl list_queues -q name messages 2>/dev/null | awk '$1=="orders.created"{print $2}')
  [ "$cur" = "$prev" ] && [ "$ready" = "0" ] && break
  prev=$cur
done
sleep 2
kill $WH $OS; wait $WH $OS 2>/dev/null
$PY experiments/analyze_queue.py "$D/ids.txt" "$D/warehouse/processed.log" "$D/orders/results.log" | sed 's/^/  /'
