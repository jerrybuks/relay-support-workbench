"""Record/check source fingerprints for independently selected teaching profiles.

Hashes detect drift; they do not replace the verification commands or prove live services.
"""

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--write", action="store_true")
args = parser.parse_args()
paths = [ROOT / "pyproject.toml", ROOT / "uv.lock", ROOT / "playwright.config.ts"]
for folder in ["src", "teaching", "tests", "browser", "evals", "scripts"]:
    paths += [p for p in (ROOT / folder).rglob("*") if p.is_file() and "__pycache__" not in p.parts]
files = {
    str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)
}
manifest = {
    "algorithm": "sha256",
    "scope": "source/tests/fixtures/locks; no runtime or evidence",
    "files": files,
}
target = ROOT / "checkpoint-files.json"
if args.write:
    target.write_text(json.dumps(manifest, indent=2) + "\n")
else:
    expected = json.loads(target.read_text())
    if expected != manifest:
        raise SystemExit("Checkpoint source drift. Reverify changes, then regenerate fingerprints.")
print(f"Checkpoint fingerprints {'recorded' if args.write else 'verified'}: {len(files)} files")
