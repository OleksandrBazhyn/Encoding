#!/usr/bin/env bash
# Експеримент 3, додатково: ідемпотентність, коли сервер падає між спробами клієнта.
# Затримка 1500 мс, дедлайн 1000/2000/4000 мс, пауза перед повтором 3000 мс.
# Перша спроба падає за таймаутом, сервер створює замовлення і публікує OrderCreated,
# потім його вбивають kill -9 і запускають знову, і лише після цього приходить повтор.
cd "$(dirname "$0")/.."
PY=.venv/bin/python
N=${N:-5}
SRV_ARGS="--schema v1 --port 50097 --idempotent --delay-ms 1500"

run() {  # $1 назва, $2 restart|norestart
  local D=logs/idem_restart/$1
  rm -rf "$D"; mkdir -p "$D"
  for q in orders.created orders.results; do docker exec shop-rabbitmq rabbitmqctl purge_queue "$q" >/dev/null 2>&1; done
  $PY warehouse.py --schema v1 --ack-mode after --confirm --log-dir "$D/warehouse" > "$D/wh.log" 2>&1 &
  local wh=$!
  local k=0
  $PY order_service.py $SRV_ARGS --log-dir "$D/srv_$k" > "$D/srv_$k.log" 2>&1 &
  local srv=$!
  sleep 1.5
  for i in $(seq 1 "$N"); do
    local before
    before=$(cat "$D/srv_$k/created.log" 2>/dev/null | wc -l)
    node client/client.js --schema v1 --addr 127.0.0.1:50097 retry --n 1 --deadline 1000 --attempts 3 --backoff 3000 \
      > "$D/client_$i.json" &
    local cl=$!
    if [ "$2" = restart ]; then
      # чекаємо, поки поточний екземпляр створить замовлення першої спроби, і вбиваємо його
      until [ "$(cat "$D/srv_$k/created.log" 2>/dev/null | wc -l)" -gt "$before" ]; do sleep 0.05; done
      sleep 0.2
      kill -9 $srv; wait $srv 2>/dev/null
      k=$((k + 1))
      $PY order_service.py $SRV_ARGS --log-dir "$D/srv_$k" > "$D/srv_$k.log" 2>&1 &
      srv=$!
    fi
    wait $cl
  done
  sleep 3
  kill $srv $wh; wait $srv $wh 2>/dev/null
  local ok
  ok=$(grep -h '"ok"' "$D"/client_*.json | grep -c ': 1')
  echo "  клієнт вважає успішними: $ok з $N"
  echo "  створено замовлень на всіх екземплярах сервера: $(cat "$D"/srv_*/created.log | wc -l), різних request_id: $(awk '{print $2}' "$D"/srv_*/created.log | sort -u | wc -l)"
  echo "  у пам'яті останнього екземпляра: $(wc -l < "$D/srv_$k/created.log")"
  echo "  склад зарезервував товар під замовлень: $(wc -l < "$D/warehouse/processed.log")"
  echo "  результати складу на сервісі: $(cat "$D"/srv_*/results.log 2>/dev/null | awk '{print $3}' | sort | uniq -c | tr -s ' ' | tr '\n' ',')"
}

echo "=== без перезапуску сервера (контроль)"
run norestart norestart
echo "=== kill -9 і перезапуск сервера між спробами"
run restart restart
