from __future__ import annotations

import xml.etree.ElementTree as ET

import requests

NEOFORGE_MAVEN = "https://maven.neoforged.net/releases/net/neoforged/neoforge"


def resolve_neoforge_version(mc_version: str, requested: str) -> str:
    """Return a concrete NeoForge version string (e.g. '21.1.233') for mc_version."""
    if requested not in ("latest", "recommended"):
        return requested
    meta_url = f"{NEOFORGE_MAVEN}/maven-metadata.xml"
    resp = requests.get(meta_url, timeout=30)
    resp.raise_for_status()
    root = ET.fromstring(resp.text)
    # NeoForge versions for MC 1.21.1 start with "21.1."
    parts = mc_version.split(".")
    prefix = f"{parts[0]}.{parts[1]}."
    versions = [
        v.text
        for v in root.findall(".//version")
        if v.text and v.text.startswith(prefix)
    ]
    if not versions:
        raise ValueError(f"No NeoForge versions found for Minecraft {mc_version}")
    return versions[-1]


def get_installer_url(neoforge_version: str) -> str:
    """Return the NeoForge server installer JAR download URL."""
    return f"{NEOFORGE_MAVEN}/{neoforge_version}/neoforge-{neoforge_version}-installer.jar"
