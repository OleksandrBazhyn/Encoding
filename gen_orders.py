"""Генерує тестові замовлення з фіксованим seed у data/orders.json."""
import argparse
import json
import random
import uuid
from pathlib import Path

CITIES = [
    ("UA", "Київ", "01001"), ("UA", "Львів", "79000"), ("UA", "Харків", "61000"),
    ("UA", "Одеса", "65000"), ("UA", "Дніпро", "49000"), ("UA", "Вінниця", "21000"),
    ("PL", "Warszawa", "00-001"), ("PL", "Kraków", "30-001"), ("DE", "Berlin", "10115"),
]
STREETS = ["Хрещатик", "Шевченка", "Franka", "Грушевського", "Сагайдачного",
           "Lesi Ukrainky", "Bandery", "Marszałkowska", "Unter den Linden"]
COMMENTS = [
    "Подзвоніть за годину до доставки",
    "Залиште біля дверей",
    "Домофон не працює, наберіть на телефон",
    "Потрібен паперовий чек",
    "Доставка після 18:00",
    "Please do not ring the bell",
]
PROMOS = ["AUTUMN10", "WELCOME5", "FREESHIP", "BLACKFRIDAY25", "STUDENT15"]


def generate(n, seed):
    rnd = random.Random(seed)
    customers = [f"cust-{i:05d}" for i in range(n // 20)]
    products = [f"SKU-{i:06d}" for i in range(5000)]
    base_ts = 1_761_000_000_000
    orders = []
    for i in range(n):
        country, city, postal = rnd.choice(CITIES)
        order = {
            "id": str(uuid.UUID(int=rnd.getrandbits(128), version=4)),
            "customer_id": rnd.choice(customers),
            "created_at_ms": base_ts + i * 1000 + rnd.randint(0, 999),
            "status": "PENDING",
            "shipping_address": {
                "country": country,
                "city": city,
                "street": f"вул. {rnd.choice(STREETS)}, {rnd.randint(1, 200)}, кв. {rnd.randint(1, 300)}",
                "postal_code": postal,
            },
            "items": [
                {
                    "product_id": rnd.choice(products),
                    "quantity": rnd.randint(1, 10),
                    "unit_price_cents": rnd.randint(500, 500_000),
                }
                for _ in range(rnd.randint(1, 20))
            ],
        }
        if rnd.random() < 0.4:
            order["comment"] = rnd.choice(COMMENTS)
        if rnd.random() < 0.3:
            order["promo_code"] = rnd.choice(PROMOS)
        orders.append(order)
    return orders


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=10_000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("-o", default="data/orders.json")
    args = ap.parse_args()
    orders = generate(args.n, args.seed)
    Path(args.o).parent.mkdir(parents=True, exist_ok=True)
    with open(args.o, "w", encoding="utf-8") as f:
        json.dump(orders, f, ensure_ascii=False)
    with_comment = sum("comment" in o for o in orders)
    items = [len(o["items"]) for o in orders]
    print(f"{len(orders)} замовлень, з коментарем {with_comment}, "
          f"позицій від {min(items)} до {max(items)}, унікальних id {len({o['id'] for o in orders})}")
