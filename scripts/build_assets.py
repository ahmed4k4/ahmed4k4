#!/usr/bin/env python3
"""Generate the Ahmed4k4 engineering banner as a standalone SVG."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"

def main():
    ASSETS.mkdir(exist_ok=True)
    # The checked-in SVG is the source of truth. This script validates its presence.
    banner = ASSETS / "banner.svg"
    if not banner.exists() or "Ahmed Adel" not in banner.read_text(encoding="utf-8"):
        raise SystemExit("assets/banner.svg is missing or does not identify Ahmed Adel")
    print("Verified assets/banner.svg")

if __name__ == "__main__":
    main()
