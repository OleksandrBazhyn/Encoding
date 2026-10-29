"""Експеримент 2, окремий випадок: v1 декодує повідомлення v2 і кодує знову.
   python reencode.py write <in.json-index> <out.bin>   (схема v2) записати замовлення
   python reencode.py pass <in.bin> <out.bin>           (схема v1) декодувати і закодувати знову
   python reencode.py show <in.bin>                     (схема v2) показати, що збереглося"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import json  # noqa: E402
import shop  # noqa: E402

cmd = sys.argv[1]
pb2, _ = shop.load_schema({"write": "v2", "pass": "v1", "show": "v2"}[cmd])
if cmd == "write":
    d = json.load(open(shop.ROOT / "data" / "orders.json", encoding="utf-8"))[int(sys.argv[2])]
    Path(sys.argv[3]).write_bytes(shop.order_from_dict(pb2, d).SerializeToString())
elif cmd == "pass":
    raw = Path(sys.argv[2]).read_bytes()
    o = pb2.Order.FromString(raw)
    o.status = pb2.CONFIRMED  # змінюємо відоме поле, як це зробив би реальний сервіс
    out = o.SerializeToString()
    Path(sys.argv[3]).write_bytes(out)
    print(f"python v1: прочитано {len(raw)} B, {shop.describe(o)}, записано {len(out)} B")
else:
    raw = Path(sys.argv[2]).read_bytes()
    print(f"v2 читає {len(raw)} B: {shop.describe(pb2.Order.FromString(raw))}")
