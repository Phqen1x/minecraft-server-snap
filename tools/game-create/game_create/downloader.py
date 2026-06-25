from __future__ import annotations

import shutil
from pathlib import Path

import requests
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)


def download_file(url: str, dest: Path, label: str | None = None) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    display = label or dest.name

    with Progress(
        TextColumn(f"[cyan]{display}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
    ) as progress:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        total = int(response.headers.get("content-length", 0))
        task = progress.add_task("", total=total or None)

        with open(dest, "wb") as f:
            for chunk in response.iter_content(chunk_size=65536):
                f.write(chunk)
                progress.advance(task, len(chunk))


def resolve_mod(mod, dest_dir: Path, pack_dir: Path, label_prefix: str = "") -> Path:
    """Return the local path for a mod, downloading or copying as needed."""
    if mod.path:
        src = (pack_dir / mod.path).resolve()
        if not src.exists():
            raise FileNotFoundError(f"Mod '{mod.name}': local path not found: {src}")
        dest = dest_dir / src.name
        if not dest.exists():
            print(f"  [copy] {mod.name}")
            shutil.copy2(src, dest)
        else:
            print(f"  [skip] {mod.name} (already present)")
        return dest
    else:
        filename = mod.url.split("/")[-1].split("?")[0]
        dest = dest_dir / filename
        if not dest.exists():
            download_file(mod.url, dest, label=f"{label_prefix}{mod.name}")
        else:
            print(f"  [skip] {mod.name} (already downloaded)")
        return dest


def download_mods(mods, dest_dir: Path, label_prefix: str = "", pack_dir: Path | None = None) -> list[Path]:
    dest_dir.mkdir(parents=True, exist_ok=True)
    pack_dir = pack_dir or Path(".")
    return [resolve_mod(mod, dest_dir, pack_dir, label_prefix) for mod in mods]
