#!/usr/bin/env bash
# Експеримент 1: час відповіді CreateOrder, 1 прогрівальний + 5 вимірювальних запусків по 10 000 викликів
# Використання: experiments/bench_rpc.sh [--with-broker]
cd "$(dirname "$0")/.."
EXTRA="--no-broker"; [ "$1" = "--with-broker" ] && EXTRA=""
.venv/bin/python order_service.py --schema v1 --port 50061 $EXTRA --log-dir logs/bench > /dev/null 2>&1 &
PID=$!
trap 'kill $PID' EXIT
sleep 1.5
echo "warmup: $(node client/client.js --schema v1 --addr 127.0.0.1:50061 create-all --n 10000)"
for i in 1 2 3 4 5; do
  echo "run$i: $(node client/client.js --schema v1 --addr 127.0.0.1:50061 create-all --n 10000)"
done
