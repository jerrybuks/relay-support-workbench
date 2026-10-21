"""Compatibility entrypoint: smoke the complete prepared RAG runtime, not only a schema."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.contact1_preflight import main  # noqa: E402

if __name__ == "__main__":
    if "--live" not in sys.argv:
        sys.argv.append("--live")
    raise SystemExit(main())
