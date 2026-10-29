"""Hex-дамп невеликого замовлення у Protobuf і JSON для розбору у звіті."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shop  # noqa: E402

pb2, _ = shop.load_schema("v1")
d = {
    "id": "o-1", "customer_id": "cust-7", "created_at_ms": 1761000000000, "status": "PENDING",
    "shipping_address": {"country": "UA", "city": "Київ", "street": "Хрещатик 1", "postal_code": "01001"},
    "items": [{"product_id": "SKU-42", "quantity": 3, "unit_price_cents": 129900}],
    "comment": "Без дзвінка",
}
b = pb2.Order.FromString(shop.order_from_dict(pb2, d).SerializeToString()).SerializeToString()
j = json.dumps(d, ensure_ascii=False, separators=(",", ":")).encode()
print(f"protobuf {len(b)} B, json {len(j)} B")
for i in range(0, len(b), 16):
    chunk = b[i:i + 16]
    print(f"{i:04x}  {' '.join(f'{x:02x}' for x in chunk):<48}")
print(j.decode())
