"""Intentionally broken, isolated teaching fixture. Never imported by the app."""


def apply_event(ledger, event):
    ledger.append({"event_id": event["id"], "amount": event["amount"]})
    return sum(item["amount"] for item in ledger)
