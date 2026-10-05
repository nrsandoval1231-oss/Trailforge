"""Build the approved Trailforge Jade palette sheet with bundled outlined fonts."""
from pathlib import Path
import json
import cairosvg
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "exports"
MANROPE = ROOT / "fonts" / "Manrope.ttf"
MONO = ROOT / "fonts" / "IBMPlexMono-Regular.ttf"
COLORS = [
    ("Deep Jade", "#126653", "18, 102, 83", "Primary action · identity signature"),
    ("Graphite", "#232B26", "35, 43, 38", "Primary text · navigation · dark ground"),
    ("Warm Paper", "#F5F4EE", "245, 244, 238", "Main canvas · generous reading space"),
    ("Mist", "#EEF4EF", "238, 244, 239", "Secondary surface · quiet grouping"),
    ("Mint", "#70D1AE", "112, 209, 174", "Route accent · emphasis on graphite"),
    ("Brass", "#B49A60", "180, 154, 96", "Restrained detail · labels on graphite"),
]


def outlined(text, path, color, x, baseline, height, weight=None):
    font = TTFont(path)
    if weight and "fvar" in font:
        from fontTools.varLib.instancer import instantiateVariableFont
        font = instantiateVariableFont(font, {"wght": weight}, inplace=False)
    glyphs, cmap, metrics = font.getGlyphSet(), font.getBestCmap(), font["hmtx"].metrics
    upm, cursor, parts = font["head"].unitsPerEm, 0, []
    for char in text:
        name = cmap.get(ord(char))
        if name:
            pen = SVGPathPen(glyphs)
            glyphs[name].draw(pen)
            d = pen.getCommands()
            if d:
                parts.append(f'<path transform="translate({cursor} 0)" d="{d}"/>')
            cursor += metrics[name][0]
        else:
            cursor += upm // 3
    font.close()
    scale = height / upm
    return f'<g fill="{color}" transform="translate({x} {baseline}) scale({scale:g} {-scale:g})">{"".join(parts)}</g>'


def main():
    chunks = ['<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1100" viewBox="0 0 1600 1100" role="img" aria-label="Trailforge Jade approved color palette">',
      '<rect width="1600" height="1100" fill="#F5F4EE"/>',
      '<path d="M0 0H1600V18H0Z" fill="#126653"/>',
      outlined("TRAILFORGE JADE", MANROPE, "#232B26", 90, 118, 42, 800),
      outlined("APPROVED IDENTITY / 03 OCTOBER 2026", MONO, "#59645D", 92, 158, 15),
      outlined("Find the project. Forge the path.", MANROPE, "#126653", 92, 220, 32, 700),
      '<path d="M90 254H1510" stroke="#D8DED8" stroke-width="2"/>',
      outlined("COLOR PALETTE", MONO, "#59645D", 92, 292, 16),
    ]
    xs, ys, w, h = (90, 820), (330, 520, 710), 660, 170
    for i, (name, hexcode, rgb, role) in enumerate(COLORS):
        x, y = xs[i % 2], ys[i // 2]
        chunks.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="#FFFFFF" stroke="#D8DED8" stroke-width="2"/>')
        # A bounded sample swatch keeps the color identity distinct from its neutral card.
        chunks.append(f'<rect x="{x+26}" y="{y+20}" width="124" height="130" rx="5" fill="{hexcode}" stroke="#D8DED8" stroke-width="1"/>')
        ink = "#FFFFFF" if name in ("Deep Jade", "Graphite") else "#232B26"
        chunks.append(outlined(name, MANROPE, "#232B26", x+202, y+52, 25, 800))
        chunks.append(outlined(hexcode, MONO, "#126653", x+202, y+85, 18))
        chunks.append(outlined(f"RGB  {rgb}", MONO, "#59645D", x+202, y+113, 14))
        chunks.append(outlined(role, MANROPE, "#59645D", x+202, y+145, 13, 500))
    chunks += ['<path d="M90 920H1510" stroke="#D8DED8" stroke-width="2"/>',
      outlined("MANROPE  /  EDITORIAL + PRODUCT", MANROPE, "#232B26", 92, 975, 18, 700),
      outlined("IBM PLEX MONO  /  TECHNICAL DETAIL", MONO, "#59645D", 92, 1010, 15),
      outlined("Screen RGB values are authoritative. Print conversions require a profile and press proof.", MANROPE, "#59645D", 92, 1050, 14, 500), '</svg>']
    svg = '\n'.join(chunks) + '\n'
    (OUT / "svg" / "color-palette.svg").write_text(svg, encoding="utf-8")
    cairosvg.svg2png(bytestring=svg.encode(), write_to=str(OUT / "png" / "color-palette-1600.png"), output_width=1600, output_height=1100)


if __name__ == "__main__":
    main()
