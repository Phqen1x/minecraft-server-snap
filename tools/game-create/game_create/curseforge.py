from __future__ import annotations

import json
import zipfile
from pathlib import Path

import requests


CF_API = "https://api.curseforge.com/v1"


def parse_cf_zip(zip_path: Path) -> tuple[dict, bool]:
    """Parse manifest.json from a CurseForge modpack zip. Returns (manifest, has_overrides)."""
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        with zf.open("manifest.json") as f:
            manifest = json.load(f)
    has_overrides = any(
        n.startswith("overrides/") and not n.endswith("/") for n in names
    )
    return manifest, has_overrides


def parse_loader(manifest: dict) -> tuple[str, str]:
    """
    Return (loader_type, loader_version) from a CurseForge manifest.
    e.g. ("fabric", "0.15.7") from modLoaders id "fabric-0.15.7".
    """
    loaders = manifest["minecraft"]["modLoaders"]
    primary = next((ml for ml in loaders if ml.get("primary")), loaders[0])
    loader_id = primary["id"]
    for prefix in ("fabric-", "forge-", "quilt-", "neoforge-"):
        if loader_id.startswith(prefix):
            return prefix.rstrip("-"), loader_id[len(prefix):]
    raise ValueError(f"Unknown mod loader: {loader_id!r}")


def _side_from_game_versions(game_versions: list[str]) -> str:
    has_client = "Client" in game_versions
    has_server = "Server" in game_versions
    if has_client and not has_server:
        return "client"
    if has_server and not has_client:
        return "server"
    return "both"


def resolve_files(files: list[dict], api_key: str) -> list[dict]:
    """
    Resolve CurseForge file IDs to download URLs via the API.
    Skips files where required=false.
    Returns list of dicts: name, fileName, url, side, fileSize.
    """
    headers = {
        "x-api-key": api_key.strip(),
        "Accept": "application/json",
        "User-Agent": "game-create/1.0",
    }
    required_files = [f for f in files if f.get("required", True)]
    file_ids = [f["fileID"] for f in required_files]

    resp = requests.post(
        f"{CF_API}/mods/files",
        json={"fileIds": file_ids},
        headers=headers,
        timeout=30,
    )
    if resp.status_code == 403:
        raise ValueError(
            f"CurseForge API returned 403. Response: {resp.text[:200]!r}\n"
            "Check your API key at https://console.curseforge.com/"
        )
    resp.raise_for_status()
    data = {fd["id"]: fd for fd in resp.json()["data"]}

    results = []
    missing = []

    for f in required_files:
        fid = f["fileID"]
        fd = data.get(fid)
        if not fd:
            missing.append(fid)
            continue

        url = fd.get("downloadUrl")
        if not url:
            # Mod author opted out of third-party distribution; use CDN fallback
            fname = fd["fileName"]
            url = f"https://mediafilez.forgecdn.net/files/{fid // 1000}/{fid % 1000}/{fname}"

        results.append({
            "name": fd.get("displayName", fd["fileName"]),
            "fileName": fd["fileName"],
            "url": url,
            "side": _side_from_game_versions(fd.get("gameVersions", [])),
            "fileSize": fd.get("fileLength", 0),
        })

    if missing:
        raise ValueError(f"CurseForge API returned no data for file IDs: {missing}")

    return results


def extract_overrides(zip_path: Path, dest_dir: Path) -> None:
    """Extract the overrides/ directory from a CurseForge zip into dest_dir."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.namelist():
            if not member.startswith("overrides/"):
                continue
            rel = member[len("overrides/"):]
            if not rel:
                continue
            dest = dest_dir / rel
            if member.endswith("/"):
                dest.mkdir(parents=True, exist_ok=True)
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(member) as src:
                    dest.write_bytes(src.read())
