from __future__ import annotations

import xml.etree.ElementTree as ET

import requests

FORGE_MAVEN = "https://maven.minecraftforge.net/net/minecraftforge/forge"


def resolve_forge_version(mc_version: str, requested: str) -> str:
    """Return a concrete Forge build version string (e.g. '47.3.0') for mc_version."""
    if requested not in ("latest", "recommended"):
        return requested
    meta_url = f"{FORGE_MAVEN}/maven-metadata.xml"
    resp = requests.get(meta_url, timeout=30)
    resp.raise_for_status()
    root = ET.fromstring(resp.text)
    prefix = f"{mc_version}-"
    versions = [
        v.text
        for v in root.findall(".//version")
        if v.text and v.text.startswith(prefix)
    ]
    if not versions:
        raise ValueError(f"No Forge versions found for Minecraft {mc_version}")
    # Maven metadata lists oldest first; last entry is newest.
    return versions[-1].split("-", 1)[1]


def get_installer_url(mc_version: str, forge_version: str) -> str:
    """Return the Forge server installer JAR download URL."""
    v = f"{mc_version}-{forge_version}"
    return f"{FORGE_MAVEN}/{v}/forge-{v}-installer.jar"
