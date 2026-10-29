"""Сервіс замовлень: gRPC сервер (частина A), публікує OrderCreated і споживає ReservationResult (частина B)."""
import argparse
import logging
import queue
import threading
import time
import uuid
from concurrent import futures
from pathlib import Path

import grpc
import pika

import shop

log = logging.getLogger("orders")


class Publisher(threading.Thread):
    """Окремий потік з власним з'єднанням: pika BlockingConnection не потокобезпечний."""

    def __init__(self, transient=False):
        super().__init__(daemon=True)
        self.transient = transient
        self.q = queue.Queue()
        self.published = 0

    def run(self):
        conn = pika.BlockingConnection(pika.URLParameters(shop.AMQP_URL))
        ch = conn.channel()
        ch.queue_declare(shop.Q_CREATED, durable=True)
        ch.confirm_delivery()
        mode = pika.DeliveryMode.Transient if self.transient else pika.DeliveryMode.Persistent
        props = pika.BasicProperties(delivery_mode=mode)
        while True:
            try:
                body = self.q.get(timeout=1)
            except queue.Empty:
                conn.process_data_events(0)
                continue
            # з confirm_delivery виклик чекає підтвердження від брокера
            ch.basic_publish("", shop.Q_CREATED, body, props, mandatory=True)
            self.published += 1


class ResultConsumer(threading.Thread):
    def __init__(self, service):
        super().__init__(daemon=True)
        self.service = service

    def run(self):
        conn = pika.BlockingConnection(pika.URLParameters(shop.AMQP_URL))
        ch = conn.channel()
        ch.queue_declare(shop.Q_RESULTS, durable=True)
        ch.basic_qos(prefetch_count=200)
        ch.basic_consume(shop.Q_RESULTS, self.on_message)
        ch.start_consuming()

    def on_message(self, ch, method, props, body):
        try:
            res = self.service.pb2.ReservationResult.FromString(body)
        except Exception as e:
            log.error("не вдалося декодувати результат: %s", e)
            ch.basic_ack(method.delivery_tag)
            return
        self.service.apply_result(res)
        ch.basic_ack(method.delivery_tag)


class _Pending:
    def __init__(self):
        self.done = threading.Event()
        self.order = None


class OrderService:
    def __init__(self, pb2, args, publisher):
        self.pb2 = pb2
        self.args = args
        self.publisher = publisher
        self.lock = threading.Lock()
        self.orders = {}
        self.by_customer = {}
        self.requests = {}
        Path(args.log_dir).mkdir(parents=True, exist_ok=True)
        self.created_log = open(Path(args.log_dir) / "created.log", "a", buffering=1)
        self.results_log = open(Path(args.log_dir) / "results.log", "a", buffering=1)

    # частина A

    def CreateOrder(self, req, ctx):
        if self.args.verbose:
            log.info("CreateOrder отримано: %s", shop.describe(req.order))
        pending, owner = None, True
        if self.args.idempotent and req.request_id:
            with self.lock:
                pending = self.requests.get(req.request_id)
                if pending is None:
                    pending = self.requests[req.request_id] = _Pending()
                else:
                    owner = False
            if not owner:
                pending.done.wait()
                return pending.order

        if self.args.delay_ms:
            time.sleep(self.args.delay_ms / 1000)

        order = self.pb2.Order()
        # CopyFrom переносить і невідомі цій версії поля
        order.CopyFrom(req.order)
        order.id = str(uuid.uuid4())
        order.created_at_ms = int(time.time() * 1000)
        order.status = self.pb2.PENDING
        with self.lock:
            self.orders[order.id] = order
            self.by_customer.setdefault(order.customer_id, []).append(order.id)
        self.created_log.write(f"{order.id} {req.request_id} client_active={ctx.is_active()}\n")
        if self.publisher:
            self.publisher.q.put(self.pb2.OrderCreated(order=order).SerializeToString())
        if pending:
            pending.order = order
            pending.done.set()
        return order

    def GetOrder(self, req, ctx):
        order = self.orders.get(req.id)
        if order is None:
            ctx.abort(grpc.StatusCode.NOT_FOUND, f"замовлення {req.id} не знайдено")
        if self.args.verbose:
            log.info("GetOrder віддає: %s", shop.describe(order))
        return order

    def ListCustomerOrders(self, req, ctx):
        ids = self.by_customer.get(req.customer_id, [])
        return self.pb2.ListOrdersResponse(orders=[self.orders[i] for i in ids])

    # частина B

    def apply_result(self, res):
        with self.lock:
            order = self.orders.get(res.order_id)
            if order is None:
                outcome = "unknown_order"
            elif order.status != self.pb2.PENDING:
                outcome = "duplicate"
            else:
                order.status = res.status
                outcome = "applied"
        status = self.pb2.OrderStatus.Name(res.status)
        self.results_log.write(f"{res.order_id} {status} {outcome}\n")
        if self.args.verbose:
            log.info("результат %s %s %s; order від складу: %s",
                     res.order_id, status, outcome, shop.describe(res.order))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema", default="v1", choices=shop.VERSIONS)
    ap.add_argument("--port", type=int, default=50051)
    ap.add_argument("--delay-ms", type=int, default=0, help="штучна затримка в CreateOrder")
    ap.add_argument("--idempotent", action="store_true", help="дедуплікація за request_id")
    ap.add_argument("--transient", action="store_true", help="повідомлення без збереження на диск")
    ap.add_argument("--no-broker", action="store_true", help="лише частина A")
    ap.add_argument("--log-dir", default="logs/orders")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s orders[" + args.schema + "] %(message)s")

    pb2, pb2_grpc = shop.load_schema(args.schema)
    publisher = None
    if not args.no_broker:
        publisher = Publisher(args.transient)
        publisher.start()
    service = OrderService(pb2, args, publisher)
    if not args.no_broker:
        ResultConsumer(service).start()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=16))
    pb2_grpc.add_OrderServiceServicer_to_server(service, server)
    server.add_insecure_port(f"127.0.0.1:{args.port}")
    server.start()
    log.info("слухаю 127.0.0.1:%d, схема %s, delay=%dms, idempotent=%s",
             args.port, args.schema, args.delay_ms, args.idempotent)
    server.wait_for_termination()


if __name__ == "__main__":
    main()
