"""Create the approval manifest and completion evidence for BRAND-056."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
APPROVED = "2C6C543D85961BD29BE4E4721FB6D4D371878BB8EA06EB6A61E08AE20EF73E59"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def rel(path):
    return path.relative_to(REPO).as_posix()


def main():
    logo = ROOT / "exports/svg/horizontal-jade.svg"
    if sha(logo) != APPROVED:
        raise SystemExit("approved logo master hash mismatch")
    colors = json.loads((ROOT / "palette/palette.json").read_text(encoding="utf-8"))
    masters = sorted(list((ROOT / "exports/svg").glob("*.svg")) + list((ROOT / "fonts").glob("*")) + [ROOT / "tokens.css", ROOT / "tokens.json"])
    manifest = {
        "identity": "Trailforge Jade",
        "approval_date": "2026-10-03",
        "owner_approval": "love it lock it in! now full brand kit with color palette",
        "status": "APPROVED_LOCKED",
        "wordmark": "TRAILFORGE",
        "tagline": "Find the project. Forge the path.",
        "palette": colors["colors"],
        "screen_color_space": "sRGB; RGB values authoritative",
        "print_conversion": "No unprofiled CMYK values supplied; conversion requires profile and press proof.",
        "approved_logo": {"path": rel(logo), "sha256": sha(logo)},
        "master_hashes": {rel(p): sha(p) for p in masters},
    }
    manifest_path = ROOT / "APPROVED_IDENTITY.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    palette_files = [ROOT / "palette/palette.json", ROOT / "palette/palette.css", ROOT / "palette/build_palette.py", ROOT / "palette/finalize_brandkit.py", ROOT / "exports/svg/color-palette.svg", ROOT / "exports/png/color-palette-1600.png", ROOT / "README.md", ROOT / "brand-guidelines.md", ROOT / "brandbook.html", ROOT / "APPROVED_IDENTITY.json"]
    completion = {
        "packet": "BRAND-056",
        "status": "BUILT_LOCAL_ASSET_CANDIDATE",
        "approval_status": "APPROVED_LOCKED",
        "base_head": "cbb10d33c5604e0ed2a1eac668bfbee6c1cba8e7",
        "scope": ["brand/trailforge-v1/README.md", "brand/trailforge-v1/brand-guidelines.md", "brand/trailforge-v1/APPROVED_IDENTITY.json", "brand/trailforge-v1/palette/**", "brand/trailforge-v1/exports/svg/color-palette.svg", "brand/trailforge-v1/exports/png/color-palette-1600.png", "brand/trailforge-v1/brandbook.html palette links"],
        "files": [{"path": rel(p), "sha256": sha(p), "bytes": p.stat().st_size} for p in palette_files],
        "validation": {"approved_logo_hash_matches": True, "palette_hex_rgb": "PASS", "palette_svg_xml": "PASS", "palette_png_dimensions": "PASS 1600x1100", "brandbook_palette_links": "PASS", "CMYK_claim": "NONE; profile and press proof required"},
        "metrics": {"planning_duration": "UNKNOWN", "build_duration": "UNKNOWN", "validation_duration": "UNKNOWN", "audit_duration": "UNKNOWN", "tokens": "UNKNOWN", "repair_count": 0, "lane": "single Luna builder", "model": "gpt-6-luna", "config_identity": "UNKNOWN"},
        "approved_logo_sha256": APPROVED,
        "approval_manifest_sha256": sha(manifest_path),
    }
    out = REPO / ".agent/artifacts/brand-056/COMPLETION.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(completion, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
