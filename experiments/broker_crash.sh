#!/usr/bin/env bash
# Експеримент 4, додатково: docker kill брокера з беклогом 10 000 повідомлень у orders.created.
cd "$(dirname "$0")/.."
PY=.venv/bin/python
count() { docker exec shop-rabbitmq rabbitmqctl list_queues -q name messages 2>/dev/null | awk '$1=="orders.created"{print $2}'; }
for variant in persistent transient; do
  echo "=== $variant"
  D=logs/broker_crash/$variant; rm -rf "$D"; mkdir -p "$D"
  docker exec shop-rabbitmq rabbitmqctl purge_queue orders.created >/dev/null 2>&1
  flag=""; [ $variant = transient ] && flag="--transient"
  $PY order_service.py --schema v1 --port 50096 --log-dir "$D" $flag > "$D/orders.log" 2>&1 &
  OS=$!
  sleep 1.5
  node client/client.js --schema v1 --addr 127.0.0.1:50096 create-all --n 10000 > /dev/null
  kill $OS; wait $OS 2>/dev/null
  echo "  до збою у черзі: $(count)"
  docker kill shop-rabbitmq > /dev/null
  docker start shop-rabbitmq > /dev/null
  until docker exec shop-rabbitmq rabbitmq-diagnostics -q check_running >/dev/null 2>&1; do sleep 1; done
  sleep 2
  echo "  після docker kill і старту: $(count)"
done
docker exec shop-rabbitmq rabbitmqctl purge_queue orders.created >/dev/null 2>&1
