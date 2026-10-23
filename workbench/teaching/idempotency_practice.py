"""Optional duplicate-event practice; the app uses transactional ledger idempotency."""


def apply_event_before(ledger, event):
    ledger.append({"event_id": event["id"], "amount": event["amount"]})
    return sum(item["amount"] for item in ledger)


def apply_event_reference(ledger, event):
    previous = next((item for item in ledger if item["event_id"] == event["id"]), None)
    if previous and previous["amount"] != event["amount"]:
        raise ValueError("Conflicting replay payload")
    if not previous:
        ledger.append({"event_id": event["id"], "amount": event["amount"]})
    return sum(item["amount"] for item in ledger)


def main():
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", choices=["before", "reference"], required=True)
    args = parser.parse_args()
    handler = apply_event_before if args.state == "before" else apply_event_reference
    ledger = []
    event = {"id": "evt-17", "amount": 2000}
    handler(ledger, event)
    actual = handler(ledger, event)
    print(f"State={args.state}; expected=2000; actual={actual}")
    return 0 if actual == 2000 else 1


if __name__ == "__main__":
    raise SystemExit(main())
