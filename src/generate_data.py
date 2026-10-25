"""Generate a reproducible synthetic e-commerce dataset (Jan 2023 - Dec 2024).

Each customer gets a hidden "intensity" (how engaged they are), a monthly
churn probability and a basket-size multiplier. Purchases are then simulated
month by month, with holiday seasonality and acquisition-channel quality
effects. The result has the skewed, Pareto-like revenue distribution seen in
real e-commerce data.

Output CSVs (data/raw/): products, customers, orders, order_items.
"""
import numpy as np
import pandas as pd

from .config import (DATA_RAW, END_DATE, N_CUSTOMERS, N_GUEST_ORDERS, SEED,
                     START_DATE, ensure_dirs)

# category: (n_products, min_price, max_price, min_margin, max_margin)
CATEGORIES = {
    "Electronics": (15, 40, 600, 0.15, 0.30),
    "Home & Kitchen": (20, 10, 150, 0.30, 0.50),
    "Fashion": (25, 15, 120, 0.45, 0.65),
    "Beauty": (15, 8, 60, 0.50, 0.70),
    "Sports & Outdoors": (15, 20, 250, 0.30, 0.45),
    "Books": (15, 8, 40, 0.25, 0.40),
    "Toys & Games": (10, 10, 80, 0.35, 0.50),
    "Grocery": (15, 3, 30, 0.15, 0.30),
}
COUNTRIES = {
    "United States": 0.38, "United Kingdom": 0.14, "India": 0.12, "Germany": 0.10,
    "Canada": 0.08, "Australia": 0.07, "France": 0.06, "Netherlands": 0.05,
}
CHANNELS = {
    "Organic Search": 0.30, "Paid Search": 0.22, "Social Media": 0.20,
    "Email": 0.12, "Referral": 0.10, "Affiliate": 0.06,
}
# Multiplier on customer engagement by acquisition channel
CHANNEL_QUALITY = {
    "Organic Search": 1.10, "Paid Search": 0.90, "Social Media": 0.75,
    "Email": 1.30, "Referral": 1.25, "Affiliate": 0.80,
}
SEASONALITY = {1: 0.85, 2: 0.85, 3: 0.95, 4: 0.95, 5: 1.00, 6: 1.00,
               7: 0.95, 8: 1.00, 9: 1.00, 10: 1.05, 11: 1.35, 12: 1.50}
STATUSES = ["completed", "cancelled", "returned"]
STATUS_P = [0.92, 0.05, 0.03]
CONVERSION_RATE = 0.88  # share of sign-ups who ever place an order


def _random_day(rng, period):
    return period.start_time + pd.Timedelta(days=int(rng.integers(0, period.days_in_month)))


def make_products(rng):
    rows = []
    for category, (n, lo, hi, m_lo, m_hi) in CATEGORIES.items():
        for i in range(n):
            price = round(float(np.exp(rng.uniform(np.log(lo), np.log(hi)))), 2)
            margin = rng.uniform(m_lo, m_hi)
            rows.append({
                "product_id": f"P{len(rows) + 1:04d}",
                "product_name": f"{category} Item {i + 1:02d}",
                "category": category,
                "list_price": price,
                "unit_cost": round(price * (1 - margin), 2),
            })
    return pd.DataFrame(rows)


def make_customers(rng, months):
    # Acquisition grows over time and peaks in the holiday season
    weights = np.linspace(1.0, 2.2, len(months)) * np.array([SEASONALITY[p.month] for p in months])
    month_idx = rng.choice(len(months), size=N_CUSTOMERS, p=weights / weights.sum())
    customers = pd.DataFrame({
        "customer_id": [f"C{i + 1:05d}" for i in range(N_CUSTOMERS)],
        "signup_date": [_random_day(rng, months[m]).strftime("%Y-%m-%d") for m in month_idx],
        "country": rng.choice(list(COUNTRIES), size=N_CUSTOMERS, p=list(COUNTRIES.values())),
        "acquisition_channel": rng.choice(list(CHANNELS), size=N_CUSTOMERS, p=list(CHANNELS.values())),
    })
    # Sort so customer ids follow sign-up order
    order = np.argsort(customers["signup_date"].values, kind="stable")
    customers = customers.iloc[order].reset_index(drop=True)
    customers["customer_id"] = [f"C{i + 1:05d}" for i in range(N_CUSTOMERS)]
    return customers, month_idx[order]


def simulate_orders(rng, customers, month_idx, months, products):
    n_products = len(products)
    popularity = 1 / np.arange(1, n_products + 1) ** 0.7
    popularity = rng.permutation(popularity)
    popularity /= popularity.sum()
    categories = list(CATEGORIES)
    cat_index = {c: np.flatnonzero(products["category"].values == c) for c in categories}
    prices = products["list_price"].values
    product_ids = products["product_id"].values

    orders, items = [], []

    def add_order(customer_id, date, basket, favourite):
        order_key = len(orders)
        orders.append((order_key, customer_id, date.strftime("%Y-%m-%d"),
                       rng.choice(STATUSES, p=STATUS_P)))
        for _ in range(min(1 + rng.poisson(0.6 * basket), 8)):
            if favourite is not None and rng.random() < 0.5:
                idx = rng.choice(cat_index[favourite])
            else:
                idx = rng.choice(n_products, p=popularity)
            qty = 1 + min(rng.poisson(0.3 * basket), 5)
            discount = 1.0 if rng.random() < 0.75 else rng.uniform(0.80, 0.95)
            items.append((order_key, product_ids[idx], int(qty), round(prices[idx] * discount, 2)))

    for i, row in enumerate(customers.itertuples(index=False)):
        if rng.random() > CONVERSION_RATE:
            continue
        intensity = rng.lognormal(0.0, 0.8) * CHANNEL_QUALITY[row.acquisition_channel]
        p_buy = min(0.06 + 0.12 * intensity, 0.85)
        churn = float(np.clip(0.10 / np.sqrt(intensity), 0.015, 0.45))
        basket = rng.lognormal(0.0, 0.5)
        favourite = rng.choice(categories) if rng.random() < 0.6 else None

        add_order(row.customer_id, pd.Timestamp(row.signup_date), basket, favourite)
        for m in range(month_idx[i] + 1, len(months)):
            if rng.random() < churn:
                break
            if rng.random() < min(p_buy * SEASONALITY[months[m].month], 0.95):
                for _ in range(1 + min(rng.poisson(0.2 * intensity), 3)):
                    add_order(row.customer_id, _random_day(rng, months[m]), basket, favourite)

    # Guest checkouts (no customer_id) - excluded from customer analytics
    for _ in range(N_GUEST_ORDERS):
        add_order(None, _random_day(rng, months[rng.integers(len(months))]),
                  rng.lognormal(0.0, 0.5), None)

    orders = pd.DataFrame(orders, columns=["order_key", "customer_id", "order_date", "status"])
    items = pd.DataFrame(items, columns=["order_key", "product_id", "quantity", "unit_price"])

    # Number orders chronologically
    orders = orders.sort_values(["order_date", "order_key"]).reset_index(drop=True)
    orders["order_id"] = [f"O{i + 1:06d}" for i in range(len(orders))]
    items = items.merge(orders[["order_key", "order_id"]], on="order_key")
    items = items.sort_values(["order_id"], kind="stable").reset_index(drop=True)
    items.insert(0, "order_item_id", np.arange(1, len(items) + 1))

    orders = orders[["order_id", "customer_id", "order_date", "status"]]
    items = items[["order_item_id", "order_id", "product_id", "quantity", "unit_price"]]
    return orders, items


def main():
    ensure_dirs()
    rng = np.random.default_rng(SEED)
    months = pd.period_range(START_DATE, END_DATE, freq="M")

    products = make_products(rng)
    customers, month_idx = make_customers(rng, months)
    orders, items = simulate_orders(rng, customers, month_idx, months, products)

    for name, df in [("products", products), ("customers", customers),
                     ("orders", orders), ("order_items", items)]:
        df.to_csv(DATA_RAW / f"{name}.csv", index=False)
        print(f"  {name:<12} {len(df):>7,} rows")


if __name__ == "__main__":
    main()
