"""Build deterministic Trailforge V1 vector and raster logo exports."""
from __future__ import annotations

import io
import re
import struct
from pathlib import Path

import cairosvg
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
FONT = ROOT / "fonts" / "Manrope.ttf"
MARK = "M12 16H88L74 30H46V44H76L62 58H46V88H30V30H12Z"
COLORS = {"jade": "#126653", "dark": "#232B26", "white": "#FFFFFF"}
WORD = "TRAILFORGE"


def outlined_wordmark():
    font = TTFont(FONT)
    if "fvar" in font:
        font = instantiateVariableFont(font, {"wght": 800}, inplace=False)
    glyph_set = font.getGlyphSet()
    cmap = font.getBestCmap()
    metrics = font["hmtx"].metrics
    kerning = {}
    if "kern" in font:
        for table in font["kern"].kernTables:
            kerning.update(table.kernTable)
    paths = []
    x = 0
    previous = None
    for char in WORD:
        glyph_name = cmap[ord(char)]
        if previous:
            x += kerning.get((previous, glyph_name), 0)
        pen = SVGPathPen(glyph_set)
        glyph_set[glyph_name].draw(pen)
        paths.append((x, pen.getCommands()))
        x += metrics[glyph_name][0]
        previous = glyph_name
    width = x
    font.close()
    return width, paths


WORD_WIDTH, WORD_PATHS = outlined_wordmark()


def outlined_group(color: str, scale: float, x: float, y: float) -> str:
    return (
        f'<g fill="{color}" transform="translate({x:g} {y:g}) scale({scale:g})">'
        + "".join(
            f'<path transform="translate({advance} 1500) scale(1 -1)" d="{data}"/>'
            for advance, data in WORD_PATHS
            if data
        )
        + "</g>"
    )


def text_paths(text: str, font_path: Path, color: str, x: float, baseline: float, height: float, weight: int | None = None) -> str:
    font = TTFont(font_path)
    if weight and "fvar" in font:
        font = instantiateVariableFont(font, {"wght": weight}, inplace=False)
    glyph_set, cmap, metrics = font.getGlyphSet(), font.getBestCmap(), font["hmtx"].metrics
    upm = font["head"].unitsPerEm
    scale = height / upm
    pieces, cursor = [], 0
    for char in text:
        glyph = cmap.get(ord(char))
        if glyph:
            pen = SVGPathPen(glyph_set)
            glyph_set[glyph].draw(pen)
            d = pen.getCommands()
            if d:
                pieces.append(f'<path transform="translate({cursor} 0)" d="{d}"/>')
            cursor += metrics.get(glyph, (upm // 2, 0))[0]
        else:
            cursor += upm // 3
    font.close()
    return f'<g fill="{color}" transform="translate({x} {baseline}) scale({scale:g} {-scale:g})">{"".join(pieces)}</g>'


def svg_doc(content: str, width: float, height: float) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:g} {height:g}" '
        f'width="{width:g}" height="{height:g}" role="img" aria-label="Trailforge brand mark">'
        f"{content}</svg>\n"
    )


def logo_variant(kind: str, color: str) -> tuple[str, int, int]:
    if kind == "icon":
        return svg_doc(f'<path fill="{color}" d="{MARK}"/>', 100, 100), 100, 100
    if kind == "wordmark":
        return svg_doc(outlined_group(color, 1, 0, 0), WORD_WIDTH, 1600), WORD_WIDTH, 1600
    if kind == "horizontal":
        scale, left, top, height = 0.055, 132, 5, 100
        width = left + WORD_WIDTH * scale + 10
        mark = f'<path fill="{color}" d="{MARK}"/>'
        word = outlined_group(color, scale, left, top)
        return svg_doc(mark + word, width, height), round(width), height
    if kind == "stacked":
        scale, width, height = 0.043, 470, 215
        word_width = WORD_WIDTH * scale
        left = (width - word_width) / 2
        mark_left = (width - 100) / 2
        mark = f'<path fill="{color}" transform="translate({mark_left:g} 0)" d="{MARK}"/>'
        word = outlined_group(color, scale, left, 104)
        return svg_doc(mark + word, width, height), width, height
    raise ValueError(kind)


def write_svg(path: Path, data: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data, encoding="utf-8", newline="\n")


def render_png(svg: str, path: Path, width: int, height: int, background: str | None = None):
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=width, output_height=height)
    image = Image.open(io.BytesIO(png)).convert("RGBA")
    if background:
        base = Image.new("RGBA", image.size, background)
        base.alpha_composite(image)
        image = base
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, optimize=True)


def main():
    exports = ROOT / "exports"
    for kind in ("horizontal", "stacked", "icon", "wordmark"):
        for name, color in COLORS.items():
            svg, width, height = logo_variant(kind, color)
            write_svg(exports / "svg" / f"{kind}-{name}.svg", svg)
            if kind == "icon":
                for size in (1024, 512, 192, 32, 16):
                    render_png(svg, exports / "png" / f"icon-{name}-{size}.png", size, size)
            elif kind == "horizontal":
                for width_px in (1600, 1024, 512):
                    height_px = round(width_px * height / width)
                    render_png(svg, exports / "png" / f"horizontal-{name}-{width_px}.png", width_px, height_px)

    # App icon: jade tile with the canonical symbol inset equally on every side.
    app_icon = svg_doc(
        f'<rect width="512" height="512" rx="112" fill="#126653"/>'
        f'<path d="{MARK}" fill="#FFFFFF" transform="translate(76.8 76.8) scale(3.584)"/>',
        512,
        512,
    )
    write_svg(exports / "svg" / "app-icon.svg", app_icon)
    render_png(app_icon, exports / "png" / "app-icon-512.png", 512, 512)
    app_png = Image.open(exports / "png" / "app-icon-512.png").convert("RGBA")
    app_png.resize((192, 192), Image.Resampling.LANCZOS).save(exports / "png" / "app-icon-192.png", optimize=True)
    app_png.resize((32, 32), Image.Resampling.LANCZOS).save(exports / "png" / "app-icon-32.png", optimize=True)

    # Measured construction plate; geometry remains the same master path.
    construction = svg_doc(
        f'<rect width="100" height="100" fill="#FBFCF9"/>'
        f'<path d="M0 0H100V100H0Z" fill="none" stroke="#D8DED8" stroke-width=".5"/>'
        + ''.join(f'<path d="M{x} 0V100M0 {x}H100" stroke="#E7ECE7" stroke-width=".25"/>' for x in range(10, 100, 10))
        + f'<path d="{MARK}" fill="#126653"/>'
        + '<path d="M30 30L44 16M62 58L76 44" stroke="#70D1AE" stroke-width="1" stroke-dasharray="2 2"/>',
        100, 100,
    )
    write_svg(exports / "svg" / "mark-construction.svg", construction)
    pattern = svg_doc(
        '<defs><pattern id="route" width="96" height="96" patternUnits="userSpaceOnUse">'
        '<path d="M0 72H30L50 52H96M48 96V72L68 52V24L92 0" fill="none" stroke="#126653" stroke-width="1.5" opacity=".28"/>'
        '<path d="M28 72l7-2-4 6" fill="#126653" opacity=".45"/><circle cx="50" cy="52" r="2" fill="#70D1AE"/></pattern></defs>'
        '<rect width="384" height="192" fill="#EEF4EF"/><rect width="384" height="192" fill="url(#route)"/>',
        384, 192,
    )
    write_svg(exports / "svg" / "route-pattern.svg", pattern)
    dark_pattern = svg_doc(
        pattern.replace('#EEF4EF', '#232B26').replace('#126653', '#70D1AE').replace('opacity=".28"', 'opacity=".35"').replace('opacity=".45"', 'opacity=".55"'),
        384, 192,
    )
    write_svg(exports / "svg" / "route-pattern-dark.svg", dark_pattern)
    social = svg_doc(
        '<rect width="1200" height="630" fill="#232B26"/><path d="M720 0H1200V630H560Z" fill="#303A34"/>'
        '<path d="M660 630L1000 290H1200V390L960 630Z" fill="#126653"/>'
        '<path d="M720 535H1110L1030 615H800V630H720Z" fill="#70D1AE" opacity=".22"/>'
        '<path d="M86 86H104" stroke="#70D1AE" stroke-width="4"/>'
        + text_paths("TRAILFORGE / JADE", ROOT / "fonts" / "IBMPlexMono-Regular.ttf", "#70D1AE", 86, 132, 16)
        + text_paths("Find the project.", FONT, "#F5F4EE", 86, 260, 58, 800)
        + text_paths("Forge the path.", FONT, "#70D1AE", 86, 340, 58, 700)
        + text_paths("Source facts. Buyer paths. Human judgment.", FONT, "#CFD9D1", 86, 420, 22, 500)
        + f'<path d="{MARK}" fill="#F5F4EE" transform="translate(800 170) scale(3.2)"/>', 1200, 630)
    write_svg(exports / "svg" / "trailforge-social-card.svg", social)
    report = svg_doc(
        '<rect width="1600" height="400" fill="#F5F4EE"/><path d="M0 0H1600V16H0Z" fill="#126653"/>'
        '<path d="M1120 400L1500 20H1600V120L1320 400Z" fill="#EEF4EF"/>'
        '<path d="M72 86H117" stroke="#126653" stroke-width="3"/>'
        + text_paths("FIELD NOTE / PROJECT REVIEW", ROOT / "fonts" / "IBMPlexMono-Regular.ttf", "#59645D", 72, 132, 16)
        + text_paths("What the source says.", FONT, "#232B26", 72, 238, 54, 800)
        + text_paths("What remains unknown.", FONT, "#126653", 72, 292, 28, 600)
        + f'<path d="{MARK}" fill="#126653" transform="translate(1424 88) scale(.95)"/>', 1600, 400)
    write_svg(exports / "svg" / "report-header.svg", report)
    slide = svg_doc(
        '<rect width="1920" height="1080" fill="#232B26"/><path d="M1050 1080L1800 330H1920V650L1490 1080Z" fill="#303A34"/>'
        '<path d="M1330 1080L1920 490V770L1610 1080Z" fill="#126653"/>'
        + text_paths("TRAILFORGE / JADE", ROOT / "fonts" / "IBMPlexMono-Regular.ttf", "#70D1AE", 140, 170, 24)
        + text_paths("Find the project.", FONT, "#F5F4EE", 140, 470, 96, 800)
        + text_paths("Forge the path.", FONT, "#70D1AE", 140, 585, 90, 700)
        + text_paths("Source facts. Buyer paths. Human judgment.", FONT, "#CFD9D1", 140, 700, 28, 500)
        + f'<path d="{MARK}" fill="#F5F4EE" transform="translate(1420 220) scale(3)"/>', 1920, 1080)
    write_svg(exports / "svg" / "slide-cover.svg", slide)

    # A restrained white-board proof image for decks, print and reviews.
    width, height = 1200, 420
    proof = Image.new("RGBA", (width, height), "#FFFFFF")
    horizontal, _, _ = logo_variant("horizontal", COLORS["jade"])
    _, svg_width, svg_height = logo_variant("horizontal", COLORS["jade"])
    artwork_height = round(820 * svg_height / svg_width)
    artwork = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=horizontal.encode(), output_width=820, output_height=artwork_height))).convert("RGBA")
    proof.alpha_composite(artwork, ((width - artwork.width) // 2, (height - artwork.height) // 2 - 25))
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(proof)
    try:
        mono = ImageFont.truetype(str(ROOT / "fonts" / "IBMPlexMono-Regular.ttf"), 18)
    except OSError:
        mono = ImageFont.load_default()
    caption = "FIND THE PROJECT. FORGE THE PATH."
    bounds = draw.textbbox((0, 0), caption, font=mono)
    draw.text(((width - (bounds[2] - bounds[0])) // 2, 322), caption, font=mono, fill="#59645D")
    proof.save(exports / "png" / "proof-board-white-1200x420.png", optimize=True)

    # Multi-resolution favicon ICO, plus individual favicon PNG sizes above.
    icon_paths = [exports / "png" / f"icon-jade-{n}.png" for n in (16, 32, 192)]
    favicon = Image.open(icon_paths[2]).convert("RGBA")
    favicon.save(exports / "favicon.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])

    print(f"built logo vectors and PNG exports; wordmark width {WORD_WIDTH} font units")


if __name__ == "__main__":
    main()
