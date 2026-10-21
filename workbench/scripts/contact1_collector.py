"""Verify actual Langfuse receipt using metadata only, independently of model quota."""

import argparse
import json
import logging
import os
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from teaching.observability_reference import RunObservation, collector_received  # noqa: E402


def check_collector(client, *, attempts=4, pause=time.sleep):
    report = {
        "kind": "live-metadata-only-collector-probe",
        "openai_calls": 0,
        "live_investigation_verified": False,
        "authenticated": False,
        "receipt": "not-confirmed",
        "trace_id": uuid.uuid4().hex,
    }
    if not client.auth_check():
        return report
    report["authenticated"] = True
    recorder = RunObservation(report["trace_id"], client)
    with recorder.activate() as root:
        root["metadata"] = {"purpose": "contact1-collector-preflight", "openai_calls": 0}
        with recorder.stage("configuration_inspection"):
            pass
    client.flush()
    for attempt in range(attempts):
        try:
            if collector_received(client, report["trace_id"]):
                report["receipt"] = "confirmed-by-observation-read"
                break
        except Exception:
            pass
        if attempt < attempts - 1:
            pause(2)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=ROOT / ".runtime/c1-preparation/collector.json"
    )
    args = parser.parse_args()
    required = ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_BASE_URL")
    if os.getenv("RELAY_TRACE_EXPORT") != "1" or not all(os.getenv(k) for k in required):
        parser.error("Explicit trace export and local Langfuse configuration are required")
    # Provider exception bodies/headers must not enter a public preparation log.
    logging.disable(logging.CRITICAL)
    from langfuse import Langfuse

    client = Langfuse(timeout=10, additional_headers={"x-langfuse-ingestion-version": "4"})
    try:
        report = check_collector(client)
    except Exception as exc:
        report = {
            "kind": "live-metadata-only-collector-probe",
            "openai_calls": 0,
            "receipt": "failed",
            "exception_type": type(exc).__name__,
        }
    finally:
        client.shutdown()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["receipt"] == "confirmed-by-observation-read" else 1


if __name__ == "__main__":
    raise SystemExit(main())
