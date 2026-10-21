"""Run as an intentionally red before-state, or green reference. Not a pytest test file."""

import argparse

from teaching.contact2_before import apply_event as before
from teaching.contact2_reference import apply_event as reference

parser = argparse.ArgumentParser()
parser.add_argument("--state", choices=["before", "reference"], required=True)
args = parser.parse_args()
handler = before if args.state == "before" else reference
ledger = []
event = {"id": "evt-17", "amount": 2000}
handler(ledger, event)
actual = handler(ledger, event)
print(f"State={args.state}; expected=2000; actual={actual}")
raise SystemExit(0 if actual == 2000 else 1)
