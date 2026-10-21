"""Minimal corrected fixture. Production service uses a transactional unique key."""


def apply_event(ledger, event):
    previous = next((item for item in ledger if item["event_id"] == event["id"]), None)
    if previous and previous["amount"] != event["amount"]:
        raise ValueError("Conflicting replay payload")
    if not previous:
        ledger.append({"event_id": event["id"], "amount": event["amount"]})
    return sum(item["amount"] for item in ledger)
