"""Render SVG logos to PNG.

Run on your local machine (where you can install dependencies):
    pip install cairosvg
    python render_logo.py

Output: logo.png, logo_dark.png, logo_simple.png  (all 512x512)

Then upload the PNG to BotFather using /setuserpic command.
"""
from pathlib import Path

try:
    import cairosvg
except ImportError:
    print("Install cairosvg first:  pip install cairosvg")
    raise SystemExit(1)

HERE = Path(__file__).parent

for svg_path in HERE.glob("*.svg"):
    png_path = svg_path.with_suffix(".png")
    cairosvg.svg2png(
        url=str(svg_path),
        write_to=str(png_path),
        output_width=512,
        output_height=512,
    )
    print(f"  ✓ {svg_path.name}  →  {png_path.name}")

print("Done! Upload PNG to @BotFather using /setuserpic")
