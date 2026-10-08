"""Generate a synthetic clickstream dataset (data/clickstream.csv)."""
import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

random.seed(42)

# Simple Markov chain: current page -> [(next page, probability)]
TRANSITIONS = {
    "home":     [("search", .30), ("category", .35), ("product", .15), ("exit", .20)],
    "search":   [("product", .55), ("category", .15), ("exit", .30)],
    "category": [("product", .60), ("search", .10), ("exit", .30)],
    "product":  [("cart", .25), ("category", .20), ("search", .15), ("product", .10), ("exit", .30)],
    "cart":     [("checkout", .50), ("product", .20), ("exit", .30)],
    "checkout": [("purchase", .65), ("cart", .10), ("exit", .25)],
    "purchase": [("exit", 1.0)],
}
DEVICES = ["desktop", "mobile", "tablet"]


def next_page(page):
    options, probs = zip(*TRANSITIONS[page])
    return random.choices(options, probs)[0]


def generate(n_users=500, days=14, out="data/clickstream.csv"):
    start_day = datetime(2026, 9, 1)
    rows = []
    for u in range(1, n_users + 1):
        user_id = f"U{u:04d}"
        device = random.choices(DEVICES, [.5, .4, .1])[0]
        for _ in range(random.randint(1, 4)):  # sessions per user
            t = start_day + timedelta(days=random.randint(0, days - 1),
                                      hours=random.randint(6, 23),
                                      minutes=random.randint(0, 59))
            page = "home" if random.random() < .6 else random.choice(["search", "category", "product"])
            while page != "exit":
                rows.append((user_id, t, page, device))
                page = next_page(page)
                t += timedelta(seconds=random.randint(5, 180))
    df = pd.DataFrame(rows, columns=["user_id", "timestamp", "page", "device"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"Generated {len(df)} events -> {out}")


if __name__ == "__main__":
    generate()
