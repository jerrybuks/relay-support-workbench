"""Launch one explicit C1 checkpoint with its own local database."""

import argparse
import os
import sys
from pathlib import Path

import uvicorn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("profile", choices=["before", "retrieval", "live"])
args = parser.parse_args()

if args.profile == "live":
    from teaching.contact1_live import create_app
    from teaching.responses_reference import live_client

    try:
        sdk_client, model = live_client()
    except RuntimeError as error:
        raise SystemExit(str(error)) from None

    # Optional reviewed metadata export; default remains fully local.
    trace_client = None
    if os.getenv("RELAY_TRACE_EXPORT") == "1":
        from langfuse import Langfuse

        if not all(
            os.getenv(k)
            for k in ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_BASE_URL")
        ):
            raise SystemExit("Configure Langfuse keys and base URL locally before enabling export.")
        trace_client = Langfuse(additional_headers={"x-langfuse-ingestion-version": "4"})
    app = create_app(client=sdk_client, model=model, trace_client=trace_client)
    port = 8002
elif args.profile == "retrieval":
    from teaching.contact1_reference import create_app

    app, port = create_app(), 8001
else:
    from relay.main import create_app

    app = create_app(
        os.getenv("RELAY_REFERENCE_DB", str(ROOT / ".runtime/c1-before.sqlite")),
        checkpoint="contact-1-before",
        session_cookie="relay_c1_before",
    )
    port = 8004
try:
    uvicorn.run(app, host="127.0.0.1", port=port)
finally:
    if args.profile == "live" and trace_client is not None:
        trace_client.flush()
        trace_client.shutdown()
    if args.profile == "live":
        sdk_client.close()
