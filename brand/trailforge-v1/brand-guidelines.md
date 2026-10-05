# Trailforge Jade implementation guidelines

## Signature and geometry

Use the supplied SVG as the master. The Trailmark uses a 100 × 100 coordinate grid, a 14-unit cap, a 16-unit stem, and consistent 45° stepped terminals. Keep clear space around every lockup equal to one quarter of the symbol height. The icon minimum is 24 px; the simplified favicon export may be used at 16 px. Keep horizontal signatures at least 120 px wide on screen and 35 mm in print. For print, keep the symbol at least 10 mm high. Do not stretch, rotate, outline, add gradients or shadows to, or redraw the mark.

## Color and type

Jade `#126653` is the primary action. Graphite `#232B26` anchors text and navigation. Warm paper `#F5F4EE` and mist `#EEF4EF` are quiet surfaces. Mint `#70D1AE` and brass `#B49A60` are restrained accents, suitable for text on graphite at the measured ratios in `tokens.json`. Use explicit text and shape for evidence states; color alone never carries meaning. Keep body copy at 16 px and metadata at least 12 px. Use the 4 px spacing rhythm.

The owner approved this logo and color palette on 2026-10-03. The six locked screen RGB colors are recorded in `palette/palette.json`; `exports/svg/color-palette.svg` and `exports/png/color-palette-1600.png` are the production palette sheet. RGB is authoritative. Do not infer CMYK values: print conversion requires a specified ICC profile and press proof.

Manrope handles product and editorial text. The wordmark is shipped as outlined Manrope ExtraBold paths, with no live font dependency. IBM Plex Mono marks IDs, timestamps, measurements, and technical labels. Local font files and their license texts are included. The upstream font sources are [Manrope on Google Fonts](https://fonts.google.com/specimen/Manrope) and [IBM Plex Mono on Google Fonts](https://fonts.google.com/specimen/IBM+Plex+Mono); both are distributed under the SIL Open Font License, whose included license text governs use.

## Interaction and evidence

Use the component focus ring (3 px, 2 px offset) for keyboard focus and retain readable labels for disabled controls. Keep UNKNOWN, VERIFIED, NEEDS REVIEW, and ERROR explicit. Glass may be used only where contrast remains readable; the tokens define an opaque solid fallback. Honor reduced-motion preferences, and provide an in-page motion pause control for animation. This guide uses no required motion.

## Voice and promise boundary

Be direct about what source evidence supports and candid about what remains unknown. Present customer contact as human-directed work. Do not imply forecast accuracy, verified customer intent, autonomous outreach, comprehensive discovery, or trademark clearance.
