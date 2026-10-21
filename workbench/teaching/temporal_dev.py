"""Pinned local Temporal dev service with explicit readiness and guaranteed teardown.

Used only by opt-in integration tests. Downloads the official CLI into ignored runtime storage.
"""

import asyncio
import os
import platform
import socket
import subprocess
import tarfile
import tempfile
import time
from contextlib import asynccontextmanager
from pathlib import Path

CLI_VERSION = "1.9.1"


def cli_binary():
    configured = os.getenv("RELAY_TEMPORAL_CLI")
    if configured:
        path = Path(configured).resolve(strict=True)
        return path
    system = {"Darwin": "darwin", "Linux": "linux"}.get(platform.system())
    arch = {"arm64": "arm64", "aarch64": "arm64", "x86_64": "amd64"}.get(platform.machine())
    if not system or not arch:
        raise RuntimeError("Set RELAY_TEMPORAL_CLI to an installed CLI on this platform.")
    cache = Path(__file__).parents[1] / ".runtime" / "temporal"
    cache.mkdir(parents=True, exist_ok=True)
    binary = cache / f"temporal-{CLI_VERSION}-{system}-{arch}"
    if binary.exists():
        return binary
    url = f"https://temporal.download/cli/archive/v{CLI_VERSION}?platform={system}&arch={arch}"
    with tempfile.TemporaryFile() as archive:
        # Use the official installer's curl transport; the CDN rejected urllib here.
        subprocess.run(
            ["curl", "--fail", "--location", "--silent", "--show-error", "--max-time", "90", url],
            stdout=archive,
            check=True,
        )
        archive.seek(0)
        with tarfile.open(fileobj=archive, mode="r:gz") as bundle:
            member = next(m for m in bundle.getmembers() if m.name in {"temporal", "./temporal"})
            if not member.isfile() or member.size > 256 * 1024 * 1024:
                raise RuntimeError("Unexpected Temporal CLI archive entry")
            source = bundle.extractfile(member)
            temporary = binary.with_suffix(".download")
            temporary.write_bytes(source.read())
            temporary.chmod(0o700)
            temporary.replace(binary)
    return binary


@asynccontextmanager
async def local_service(directory):
    from temporalio.client import Client

    binary = await asyncio.to_thread(cli_binary)
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    log_path = Path(directory) / "temporal-dev.log"
    with log_path.open("w") as log:
        process = subprocess.Popen(
            [
                str(binary),
                "server",
                "start-dev",
                "--ip",
                "127.0.0.1",
                "--port",
                str(port),
                "--headless",
                "--log-level",
                "warn",
            ],
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        try:
            deadline = time.monotonic() + 30
            while True:
                if process.poll() is not None:
                    raise RuntimeError(
                        "Temporal dev server exited: " + log_path.read_text()[-2000:]
                    )
                try:
                    client = await asyncio.wait_for(Client.connect(f"127.0.0.1:{port}"), timeout=1)
                    break
                except (RuntimeError, TimeoutError):
                    if time.monotonic() >= deadline:
                        raise RuntimeError("Temporal service was not ready within 30s") from None
                    await asyncio.sleep(0.1)
            yield client
        finally:
            process.terminate()
            try:
                await asyncio.to_thread(process.wait, timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                await asyncio.to_thread(process.wait, timeout=5)
