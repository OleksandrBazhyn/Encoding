"""Експеримент 1: розмір і час кодування JSON та Protobuf (Python) на 10 000 замовлень."""
import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import shop  # noqa: E402

RUNS = 5


def main():
    pb2, _ = shop.load_schema("v1")
    data = json.load(open(shop.ROOT / "data" / "orders.json", encoding="utf-8"))
    # однаковий набір полів для обох форматів: схема v1 не має promo_code
    dicts = [{k: v for k, v in d.items() if k != "promo_code"} for d in data]
    msgs = [shop.order_from_dict(pb2, d) for d in dicts]

    def json_enc():
        return [json.dumps(d, ensure_ascii=False, separators=(",", ":")).encode() for d in dicts]

    def pb_enc():
        return [m.SerializeToString() for m in msgs]

    json_bytes, pb_bytes = json_enc(), pb_enc()

    def json_dec():
        return [json.loads(b) for b in json_bytes]

    def pb_dec():
        return [pb2.Order.FromString(b) for b in pb_bytes]

    results = {}
    for name, fn in [("json_encode", json_enc), ("json_decode", json_dec),
                     ("pb_encode", pb_enc), ("pb_decode", pb_dec)]:
        fn()  # прогрів
        times = []
        for _ in range(RUNS):
            t0 = time.perf_counter()
            fn()
            times.append((time.perf_counter() - t0) * 1000)
        results[name] = statistics.median(times)
        print(f"{name:12s} runs(ms)={[round(t, 1) for t in times]} median={results[name]:.1f}")

    js = sum(map(len, json_bytes))
    pbs = sum(map(len, pb_bytes))
    print(f"size json={js} protobuf={pbs} ratio={js / pbs:.2f}")
    print(f"avg per order: json={js / len(dicts):.0f} B, protobuf={pbs / len(dicts):.0f} B")
    print(json.dumps({"json_bytes": js, "pb_bytes": pbs, **{k: round(v, 2) for k, v in results.items()}}))


if __name__ == "__main__":
    main()
