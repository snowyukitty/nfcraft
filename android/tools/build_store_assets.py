"""Compose store editorial artwork from the existing reviewed IconFlow asset.

This does not generate or modify launcher icons. Run with the repository venv
(Pillow required). Fonts are the app's bundled OFL-licensed originals.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ANDROID = Path(__file__).resolve().parents[1]
STORE = ANDROID / "store"
FONTS = ANDROID / "app/src/main/assets/fonts"


def build() -> None:
    scale = 2
    image = Image.new("RGB", (1024 * scale, 500 * scale), "#fff4de")
    draw = ImageDraw.Draw(image)

    def text(x: int, y: int, value: str, size: int, *, mono: bool = False,
             color: str = "#214b40") -> None:
        font = ImageFont.truetype(str(FONTS / ("SpaceMono-Regular.ttf" if mono
                                             else "BricolageGrotesque.ttf")), size * scale)
        draw.text((x * scale, y * scale), value, font=font, fill=color,
                  stroke_width=0)

    draw.rectangle((690 * scale, 0, 1024 * scale, 500 * scale), fill="#214b40")
    text(60, 42, "nfcraft", 32)
    text(57, 127, "Good links.", 64)
    text(57, 202, "Made tangible.", 64)
    draw.line((62 * scale, 314 * scale, 593 * scale, 314 * scale),
              fill="#d2c8b4", width=scale)
    text(62, 342, "Write. Verify. Reuse.", 21, mono=True)
    text(62, 395, "An NFC workshop in your pocket.", 20)

    # Reuse the reviewed identity as supplied; its forest field matches this panel.
    with Image.open(STORE / "google-play-icon.png") as source:
        mark = source.convert("RGB").resize((256 * scale, 256 * scale), Image.Resampling.LANCZOS)
    image.paste(mark, (729 * scale, 88 * scale))
    text(704, 365, "NTAG213 / 215 / 216", 18, mono=True, color="#fff4de")
    target = STORE / "feature-graphic.png"
    image.resize((1024, 500), Image.Resampling.LANCZOS).save(target, optimize=True)
    print(f"Created {target.relative_to(ANDROID)} (1024 x 500, RGB)")


if __name__ == "__main__":
    build()
