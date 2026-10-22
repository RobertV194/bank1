"""Генератор синтетичних подій клієнтів."""
import numpy as np
import pandas as pd

from .config import DATA_PATH, RANDOM_STATE


def generate_events(n_users: int = 1500, n_products: int = 200, seed: int = RANDOM_STATE) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    prices = np.round(rng.lognormal(mean=3.5, sigma=0.7, size=n_products), 2)
    start = pd.Timestamp("2024-01-01")
    rows = []

    for user_id in range(1, n_users + 1):
        activity = rng.gamma(shape=2.0, scale=1.0)
        n_sessions = max(1, rng.poisson(1 + 2 * activity))
        for s in range(n_sessions):
            session_id = f"{user_id}-{s}"
            t = start + pd.Timedelta(minutes=int(rng.integers(0, 60 * 24 * 60)))
            for _ in range(max(1, rng.poisson(2 + 2 * activity))):
                product = int(rng.integers(0, n_products))
                t += pd.Timedelta(seconds=int(rng.integers(5, 240)))
                rows.append((t, "view", product, prices[product], user_id, session_id))
                if rng.random() < 0.25:
                    t += pd.Timedelta(seconds=int(rng.integers(5, 120)))
                    rows.append((t, "cart", product, prices[product], user_id, session_id))
                    if rng.random() < 0.4:
                        t += pd.Timedelta(seconds=int(rng.integers(5, 120)))
                        rows.append((t, "purchase", product, prices[product], user_id, session_id))

    df = pd.DataFrame(rows, columns=["event_time", "event_type", "product_id", "price", "user_id", "user_session"])
    return df.sort_values("event_time").reset_index(drop=True)


def save_synthetic_dataset(path=DATA_PATH) -> pd.DataFrame:
    path.parent.mkdir(parents=True, exist_ok=True)
    df = generate_events()
    df.to_csv(path, index=False)
    return df


if __name__ == "__main__":
    print(f"Збережено {len(save_synthetic_dataset())} подій у {DATA_PATH}")
