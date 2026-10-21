"""Reproducible local verification; never calls OpenAI or writes to external services."""

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument(
    "--with-temporal",
    action="store_true",
    help="Run actual ephemeral local Temporal servers (may download binaries)",
)
parser.add_argument(
    "--record-checkpoint",
    action="store_true",
    help="Record new source hashes only after all preceding verification checks pass",
)
args = parser.parse_args()
environment = os.environ.copy()
if args.with_temporal:
    environment["RELAY_TEMPORAL_TEST"] = "1"
commands = [
    [sys.executable, "-m", "ruff", "check", "workbench"],
    [sys.executable, "-m", "ruff", "format", "--check", "workbench"],
    ["pnpm", "format:check"],
    [sys.executable, "workbench/scripts/contact1_references.py"],
    [sys.executable, "-m", "pytest", "workbench/tests", "-q"],
    [sys.executable, "workbench/scripts/evaluate.py"],
    ["pnpm", "scan:secrets"],
    ["pnpm", "exec", "playwright", "test", "--config", "workbench/playwright.config.ts"],
    [
        sys.executable,
        "-c",
        "import sys; import relay.main; "
        "assert not any(m == 'teaching' or m.startswith('teaching.') for m in sys.modules); "
        "print('Baseline import boundary: no teaching references loaded')",
    ],
    ["uv", "build", "--project", "workbench", "--out-dir", "workbench/.runtime/dist", "--offline"],
    [
        sys.executable,
        "-c",
        "from pathlib import Path; from zipfile import ZipFile; "
        "wheel = next(Path('workbench/.runtime/dist').glob('*.whl')); "
        "names = ZipFile(wheel).namelist(); "
        "assert all('relay/static/' + p in names for p in "
        "['index.html', 'app.js', 'course.html', 'course.css', "
        "'contact1.html', 'contact1-concepts.html', 'contact1.css', 'contact1.js']); "
        "assert all('relay/static/vendor/swagger-ui/' + p in names for p in "
        "['swagger-ui-bundle.js', 'swagger-ui.css', 'LICENSE', 'provenance.json']); "
        "assert not any('teaching/' in n or '.runtime/' in n for n in names); "
        "print('Baseline wheel includes frontend assets and excludes teaching/runtime data')",
    ],
    [
        sys.executable,
        "-c",
        "from pathlib import Path; import tarfile; "
        "archive = next(Path('workbench/.runtime/dist').glob('*.tar.gz')); "
        "bundle = tarfile.open(archive); names = bundle.getnames(); bundle.close(); "
        "assert any(n.endswith('/src/relay/static/index.html') for n in names); "
        "assert not any(p in {'.runtime', '.venv', 'teaching', 'evidence', '__pycache__'} "
        "or p.startswith('.env') or p.endswith(('.sqlite', '.pyc')) "
        "for n in names for p in Path(n).parts); "
        "print('Source archive excludes runtime databases, secrets, binaries and teaching data')",
    ],
    ["git", "diff", "--check"],
]
for command in commands:
    print("\nRUN " + " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, env=environment, check=True)
if args.record_checkpoint:
    subprocess.run(
        [sys.executable, "workbench/scripts/checkpoint_files.py", "--write"],
        cwd=ROOT,
        env=environment,
        check=True,
    )
subprocess.run(
    [sys.executable, "workbench/scripts/checkpoint_files.py"],
    cwd=ROOT,
    env=environment,
    check=True,
)
print("\nRelay local verification passed. External service quality/integration is not implied.")
