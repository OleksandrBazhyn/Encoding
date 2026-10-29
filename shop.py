"""Спільне для Python-процесів: завантаження згенерованого коду потрібної версії схеми."""
import importlib
import os
import sys
from pathlib import Path

from google.protobuf.unknown_fields import UnknownFieldSet

ROOT = Path(__file__).resolve().parent
VERSIONS = ("v1", "v2", "v2break")

AMQP_URL = os.environ.get("AMQP_URL", "amqp://guest:guest@localhost:5672/%2F")
Q_CREATED = "orders.created"
Q_RESULTS = "orders.results"


def load_schema(version):
    if version not in VERSIONS:
        raise SystemExit(f"невідома версія схеми {version}, доступні: {VERSIONS}")
    # згенерований *_pb2_grpc.py імпортує shop_pb2 за коротким ім'ям
    sys.path.insert(0, str(ROOT / "gen" / "python" / version))
    pb2 = importlib.import_module("shop_pb2")
    pb2_grpc = importlib.import_module("shop_pb2_grpc")
    return pb2, pb2_grpc


def has_field(msg, name):
    return name in msg.DESCRIPTOR.fields_by_name


def order_from_dict(pb2, d):
    """dict з data/orders.json -> Order. Поля, яких немає у схемі, пропускаються."""
    o = pb2.Order(
        id=d.get("id", ""),
        customer_id=d["customer_id"],
        created_at_ms=d.get("created_at_ms", 0),
        status=pb2.OrderStatus.Value(d.get("status", "PENDING")),
    )
    a = d["shipping_address"]
    o.shipping_address.country = a["country"]
    o.shipping_address.city = a["city"]
    o.shipping_address.street = a["street"]
    o.shipping_address.postal_code = a["postal_code"]
    for it in d["items"]:
        o.items.add(product_id=it["product_id"], quantity=it["quantity"],
                    unit_price_cents=it["unit_price_cents"])
    if "comment" in d and has_field(o, "comment"):
        o.comment = d["comment"]
    if "promo_code" in d and has_field(o, "promo_code"):
        o.promo_code = d["promo_code"]
    return o


def describe(o):
    """Короткий опис замовлення для логів експериментів."""
    parts = [f"id={o.id}", f"items={len(o.items)}"]
    if o.items:
        parts.append(f"item0.qty={o.items[0].quantity}")
    if has_field(o, "comment"):
        parts.append(f"comment={o.comment!r}" if o.HasField("comment") else "comment=<не задано>")
    if has_field(o, "promo_code"):
        parts.append(f"promo_code={o.promo_code!r}")
    unknown = UnknownFieldSet(o)
    if len(unknown):
        parts.append("unknown=" + ",".join(f"#{f.field_number}" for f in unknown))
    return " ".join(parts)
