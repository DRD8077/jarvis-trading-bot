import time
import random
import argparse
from copy import deepcopy

from stock_data_fetcher import fetch_nse_option_chain, parse_option_chain_json
from data_store import init_db, save_snapshot


def perturb_number(x, scale=0.01):
    try:
        v = float(x or 0)
    except Exception:
        return x
    # small relative noise
    return v * (1 + random.normalvariate(0, scale))


def perturb_record(rec, scale=0.05):
    r = deepcopy(rec)
    # common numeric keys to perturb if present
    for k in ["openInterest", "changeinOpenInterest", "totalTradedVolume", "impliedVolatility", "lastPrice", "bidprice", "askPrice"]:
        if k in r:
            r[k] = perturb_number(r[k], scale=scale)
    return r


def synthetic_backfill(symbol: str, count: int = 500, start_ts: int = None):
    init_db()
    base = fetch_nse_option_chain(symbol)
    if base:
        calls_df, puts_df, underlying = parse_option_chain_json(base)
        calls = calls_df.to_dict(orient="records") if not calls_df.empty else []
        puts = puts_df.to_dict(orient="records") if not puts_df.empty else []
    else:
        print("Warning: NSE API blocked or unavailable, using synthetic base data for", symbol)
        # create synthetic base: ATM around 1500 with strikes
        underlying = 1500.0
        strikes = list(range(1200, 1801, 50))
        calls = []
        puts = []
        for s in strikes:
            calls.append({
                "strike": s,
                "openInterest": 1000 + (s % 200),
                "changeinOpenInterest": random.randint(-50, 100),
                "totalTradedVolume": random.randint(10, 5000),
                "impliedVolatility": round(0.15 + (abs(s - underlying) / underlying) * 0.5, 4),
                "lastPrice": max(1.0, (underlying - s) * 0.1 + random.random()),
            })
            puts.append({
                "strike": s,
                "openInterest": 1000 + (s % 230),
                "changeinOpenInterest": random.randint(-50, 100),
                "totalTradedVolume": random.randint(10, 5000),
                "impliedVolatility": round(0.15 + (abs(s - underlying) / underlying) * 0.5, 4),
                "lastPrice": max(1.0, (s - underlying) * 0.1 + random.random()),
            })

    if not start_ts:
        start_ts = int(time.time()) - count * 120

    print(f"Generating {count} synthetic snapshots for {symbol}")
    for i in range(count):
        ts = start_ts + i * 120
        # small random walk trend on underlying
        drift = random.normalvariate(0, 0.0008) + (0.0001 if i % 50 == 0 else 0)
        u = underlying * (1 + drift * i)

        calls_p = [perturb_record(c, scale=0.03) for c in calls]
        puts_p = [perturb_record(p, scale=0.03) for p in puts]

        save_snapshot(symbol, ts, float(u), calls_p, puts_p)
        if (i + 1) % 50 == 0:
            print(f"  saved {i+1}/{count}")

    print("Backfill complete")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("symbol", nargs="?", default="RELIANCE")
    p.add_argument("--count", type=int, default=500)
    args = p.parse_args()
    synthetic_backfill(args.symbol, count=args.count)
