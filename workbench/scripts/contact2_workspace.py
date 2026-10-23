"""Create a new rehearsal checkout; never reset or delete an existing workspace."""

import argparse
import json
import shutil
import sqlite3
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", default=str(ROOT.parent / "relay-contact2-class"))
    args = parser.parse_args()
    target = Path(args.path).expanduser().resolve()
    if target.exists():
        raise SystemExit(
            "Destination exists. Reuse it or choose a new --path; no reset was performed."
        )
    subprocess.run(
        ["git", "worktree", "add", "--detach", str(target), "HEAD"], cwd=ROOT, check=True
    )
    subprocess.run(
        ["uv", "sync", "--project", str(target / "workbench"), "--locked", "--extra", "references"],
        check=True,
    )
    if (ROOT / "node_modules").exists():
        (target / "node_modules").symlink_to(ROOT / "node_modules", target_is_directory=True)
    # Reuse only the dedicated seed-only C2 index, never Contact 1/owner runtime data.
    source = ROOT / "workbench/.runtime/contact2"
    dest = target / "workbench/.runtime/contact2"
    manifest_path = source / "vectors/relay-manifest.json"
    seeded = False
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        original_ids = {"POL-DELIVERY-3", "POL-ADDRESS-2", "POL-DAMAGE-1", "OPS-PRIVATE-1"}
        with sqlite3.connect(source / "workshop.sqlite") as db:
            clean = db.execute("SELECT COUNT(*) FROM c2_sources").fetchone()[0] == 0
            clean = clean and db.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 0
            if clean and set(manifest["sources"]) == original_ids:
                dest.mkdir(parents=True, exist_ok=True)
                with sqlite3.connect(dest / "workshop.sqlite") as output:
                    db.backup(output)
                shutil.copytree(source / "vectors", dest / "vectors")
                seeded = True
    info = {
        "path": str(target),
        "revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=target, text=True
        ).strip(),
        "seed_index_copied": seeded,
        "credentials_copied": False,
        "skills": sorted(p.parent.name for p in (target / ".agents/skills").glob("*/SKILL.md")),
        "environment_file": str(ROOT / "workbench/.env"),
    }
    report = ROOT / "workbench/.runtime/contact2/setup.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(info, indent=2) + "\n")
    print(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
