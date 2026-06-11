from __future__ import annotations

import json
import zipfile
from pathlib import Path
import tomllib  # Python 3.11+


def detect_mod_side(jar_path: Path) -> str:
    """
    Inspects a JAR file to determine if it is client-only, server-only, or both.
    Returns: "client", "server", or "both".
    """
    try:
        with zipfile.ZipFile(jar_path) as zf:
            # Check Fabric
            if "fabric.mod.json" in zf.namelist():
                with zf.open("fabric.mod.json") as f:
                    data = json.load(f)
                    env = data.get("environment", "*")
                    if env == "client":
                        return "client"
                    if env == "server":
                        return "server"

            # Check Forge / NeoForge
            for manifest_path in ("META-INF/mods.toml", "META-INF/neoforge.mods.toml"):
                if manifest_path in zf.namelist():
                    with zf.open(manifest_path) as f:
                        data = tomllib.loads(f.read().decode("utf-8"))
                        # Some mods specify side in the mods list
                        mods = data.get("mods", [])
                        if mods and isinstance(mods, list):
                            # If all mods in the JAR are client-side
                            sides = [m.get("side", "BOTH").lower() for m in mods]
                            if all(s == "client" for s in sides):
                                return "client"
                            if all(s == "server" for s in sides):
                                return "server"
                        
                        # Check displayTest=IGNORE_SERVER_VERSION (common for client-only mods)
                        # but it's not a guarantee.
    except Exception:
        pass
    
    # Fallback for known client-only patterns if metadata is missing or ambiguous
    name_lower = jar_path.name.lower()
    client_keywords = [
        "client", "rendering", "visual", "gui", "hud", "shader", "fancy", 
        "fps", "immediatelyfast", "sodium", "iris", "embeddium", "oculus",
        "betterfps", "smoothchunk", "dynamiclights", "distancemod", "zoom",
        "inventoryhud", "appleskin", "mousewheelie", "itemscroller", 
        "controlling", "searchables", "highlighter", "jei", "rei", "emi"
    ]
    # Note: jei/rei/emi are technically both but often have client-only sub-mods
    
    # We should be conservative. If we're not sure, return "both".
    return "both"
