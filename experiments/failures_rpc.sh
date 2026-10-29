#!/usr/bin/env bash
# Експеримент 3: збої під час виклику. 20 логічних замовлень, до 3 спроб, таймаут 1000/2000/4000 мс.
cd "$(dirname "$0")/.."
PY=.venv/bin/python
OUT=logs/exp3
rm -rf "$OUT"; mkdir -p "$OUT"
N=20

run_case() {  # $1 назва, далі аргументи сервера
  local name=$1; shift
  echo "=== $name"
  $PY order_service.py --schema v1 --port 50081 --no-broker --log-dir "$OUT/$name" "$@" > "$OUT/$name.srv.log" 2>&1 &
  local pid=$!
  sleep 1.2
  node client/client.js --schema v1 --addr 127.0.0.1:50081 retry --n $N --deadline 1000 --attempts 3
  sleep 6  # даємо серверу дообробити запити, від яких клієнт уже відмовився
  kill $pid; wait $pid 2>/dev/null
  local f="$OUT/$name/created.log"
  echo "на сервері створено: $(wc -l < "$f"), різних request_id: $(awk '{print $2}' "$f" | sort -u | wc -l), створено після того як клієнт відмовився: $(grep -c 'client_active=False' "$f")"
}

echo "=== сервер не запущений"
node client/client.js --schema v1 --addr 127.0.0.1:50081 retry --n $N --deadline 1000 --attempts 3
echo "на сервері створено: 0 (процесу немає)"

run_case slow_1500 --delay-ms 1500
run_case slow_1500_idempotent --delay-ms 1500 --idempotent
run_case slow_5000 --delay-ms 5000
run_case slow_5000_idempotent --delay-ms 5000 --idempotent
