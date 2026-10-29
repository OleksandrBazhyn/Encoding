"""Звіряє відправлені й оброблені замовлення для експерименту 4.
python analyze_queue.py <ids.txt> <warehouse processed.log> <orders results.log>"""
import sys
from collections import Counter

sent = [line.strip() for line in open(sys.argv[1]) if line.strip()]
processed = Counter()
redelivered = 0
for line in open(sys.argv[2]):
    parts = line.split()
    processed[parts[0]] += 1
    redelivered += parts[-1] == "redelivered=True"
outcomes = Counter(line.split()[2] for line in open(sys.argv[3]))

sent_set = set(sent)
missing = sent_set - processed.keys()
dups = {k: v for k, v in processed.items() if v > 1}
print(f"відправлено: {len(sent)} (унікальних {len(sent_set)})")
print(f"рядків обробки на складі: {sum(processed.values())}, унікальних замовлень: {len(processed)}, "
      f"з них redelivered=True: {redelivered}")
print(f"втрачено (не оброблено жодного разу): {len(missing)}")
print(f"оброблено двічі і більше: {len(dups)} замовлень, зайвих обробок: {sum(v - 1 for v in dups.values())}")
print(f"сервіс замовлень отримав результатів: {sum(outcomes.values())} {dict(outcomes)}")
