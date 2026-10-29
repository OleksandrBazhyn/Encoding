"""Сервіс складу: читає orders.created, резервує товар, публікує ReservationResult в orders.results."""
import argparse
import logging
import time
from pathlib import Path

import pika

import shop

log = logging.getLogger("warehouse")

INITIAL_STOCK = 40


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema", default="v1", choices=shop.VERSIONS)
    ap.add_argument("--ack-mode", default="after", choices=["after", "batch", "auto"],
                    help="after: ack після обробки кожного; batch: ack пачкою; auto: брокер вважає доставленим одразу")
    ap.add_argument("--batch-size", type=int, default=100)
    ap.add_argument("--prefetch", type=int, default=100)
    ap.add_argument("--confirm", action="store_true", help="publisher confirms для результатів")
    ap.add_argument("--work-ms", type=float, default=0.5, help="імітація роботи на одне замовлення")
    ap.add_argument("--log-dir", default="logs/warehouse")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s warehouse[" + args.schema + "] %(message)s")

    pb2, _ = shop.load_schema(args.schema)
    Path(args.log_dir).mkdir(parents=True, exist_ok=True)
    processed_log = open(Path(args.log_dir) / "processed.log", "a", buffering=1)
    stock = {}

    conn = pika.BlockingConnection(pika.URLParameters(shop.AMQP_URL))
    ch = conn.channel()
    ch.queue_declare(shop.Q_CREATED, durable=True)
    ch.queue_declare(shop.Q_RESULTS, durable=True)
    if args.confirm:
        ch.confirm_delivery()
    if args.ack_mode != "auto":
        ch.basic_qos(prefetch_count=args.prefetch)
    props = pika.BasicProperties(delivery_mode=pika.DeliveryMode.Persistent)
    unacked = 0
    last_tag = None

    def flush_acks():
        # залишок пачки підтверджується раз на секунду, щоб черга не висіла в unacked
        nonlocal unacked
        if unacked:
            ch.basic_ack(last_tag, multiple=True)
            unacked = 0
        conn.call_later(1, flush_acks)

    def on_message(ch, method, _props, body):
        nonlocal unacked, last_tag
        try:
            evt = pb2.OrderCreated.FromString(body)
        except Exception as e:
            log.error("не вдалося декодувати OrderCreated (%d байт): %s", len(body), e)
            processed_log.write(f"- DECODE_ERROR redelivered={method.redelivered}\n")
            if args.ack_mode != "auto":
                ch.basic_reject(method.delivery_tag, requeue=False)
            return
        order = evt.order
        if args.verbose:
            log.info("отримано: %s", shop.describe(order))

        if args.work_ms:
            time.sleep(args.work_ms / 1000)
        ok = all(stock.get(it.product_id, INITIAL_STOCK) >= it.quantity for it in order.items)
        if ok:
            for it in order.items:
                stock[it.product_id] = stock.get(it.product_id, INITIAL_STOCK) - it.quantity
        res = pb2.ReservationResult(
            order_id=order.id,
            status=pb2.CONFIRMED if ok else pb2.REJECTED,
            reason="" if ok else "недостатньо товару",
            processed_at_ms=int(time.time() * 1000),
        )
        res.order.CopyFrom(order)
        processed_log.write(f"{order.id} {pb2.OrderStatus.Name(res.status)} redelivered={method.redelivered}\n")
        ch.basic_publish("", shop.Q_RESULTS, res.SerializeToString(), props)

        if args.ack_mode == "after":
            ch.basic_ack(method.delivery_tag)
        elif args.ack_mode == "batch":
            unacked += 1
            last_tag = method.delivery_tag
            if unacked >= args.batch_size:
                ch.basic_ack(method.delivery_tag, multiple=True)
                unacked = 0

    if args.ack_mode == "batch":
        conn.call_later(1, flush_acks)
    ch.basic_consume(shop.Q_CREATED, on_message, auto_ack=args.ack_mode == "auto")
    log.info("чекаю на %s, ack=%s, prefetch=%d", shop.Q_CREATED, args.ack_mode, args.prefetch)
    try:
        ch.start_consuming()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
