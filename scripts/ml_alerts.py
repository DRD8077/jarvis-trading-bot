#!/usr/bin/env python3
"""Scheduled ML alerts: run model inference for indices and notify subscribers."""
import os
from ml_index import load_model, predict_signal_for_latest
from data_store import list_subscribers, get_alert_threshold
from telegram_bot import send_message

TICKERS = {"NIFTY": "^NSEI", "SENSEX": "^BSESN"}


def run_alerts():
    # Load model once
    try:
        model = load_model()
    except Exception:
        model = None

    subs = list_subscribers()
    if not subs:
        print("No subscribers to notify.")
        return

    for name, ticker in TICKERS.items():
        try:
            res = predict_signal_for_latest(ticker, model=model)
            sig = res.get("signal")
            prob = float(res.get("prob", 0.0))
        except Exception as e:
            print(f"Prediction failed for {ticker}: {e}")
            continue

        for chat_id in subs:
            try:
                thr = get_alert_threshold(chat_id)
            except Exception:
                thr = 0.65

            # Only alert when model is confident
            if sig != "hold" and ((sig == "buy_calls" and prob >= thr) or (sig == "buy_puts" and prob <= (1 - thr))):
                text = f"📣 ML Alert for {name}\nSignal: {sig}\nConfidence: {prob:.2f}\nModel-driven suggestion: {sig}"
                try:
                    send_message(chat_id, text)
                except Exception:
                    print(f"Failed to notify {chat_id}")


if __name__ == "__main__":
    run_alerts()
