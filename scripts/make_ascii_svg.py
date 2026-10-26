#!/usr/bin/env python3
"""Render wadi-ascii.svg: ASCII portrait from the GitHub avatar.
Needs Pillow (pip install pillow). Chars coloured in a deep-green ramp."""
import io, sys, urllib.request
from PIL import Image, ImageEnhance, ImageOps

USER = sys.argv[1] if len(sys.argv) > 1 else "abduIwahid"
OUT = sys.argv[2] if len(sys.argv) > 2 else "wadi-ascii.svg"
COLS, ROWS, FS = 70, 42, 10
RAMP = " .:-=+*#%@"
COLORS = ["#12211C", "#1D4038", "#046A55", "#12936F", "#7EE2B8"]

def main():
    req = urllib.request.Request(f"https://github.com/{USER}.png?size=420",
                                 headers={"User-Agent": "Mozilla/5.0"})
    img = Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=60).read())).convert("L")
    w, h = img.size
    crop = int(w * 0.08)
    img = img.crop((crop, crop, w - crop, h - crop))
    img = ImageOps.autocontrast(img)
    img = ImageEnhance.Contrast(img).enhance(1.15)
    img = img.resize((COLS, ROWS))
    px = img.load()
    F = "ui-monospace,'JetBrains Mono',Menlo,monospace"
    W, H = COLS * 6, ROWS * FS
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
           f'<rect width="{W}" height="{H}" rx="10" fill="#0D1117"/>']
    for r in range(ROWS):
        spans, cur_col, buf = [], None, ""
        for c in range(COLS):
            v = 1.0 - (px[c, r] / 255.0)  # invert: bright photo background -> sparse chars, subject -> dense
            ch = RAMP[min(len(RAMP) - 1, int(v * len(RAMP)))]
            col = COLORS[min(len(COLORS) - 1, int(v * len(COLORS)))]
            if col != cur_col:
                if buf:
                    spans.append((cur_col, buf))
                cur_col, buf = col, ch
            else:
                buf += ch
        if buf:
            spans.append((cur_col, buf))
        x = 0
        parts = []
        for col, text in spans:
            esc = text.replace("&", "&amp;").replace("<", "&lt;")
            parts.append(f'<tspan x="{x}" fill="{col}">{esc}</tspan>')
            x += len(text) * 6
        out.append(f'<text y="{(r + 1) * FS - 2}" font-family="{F}" font-size="{FS}" xml:space="preserve">{"".join(parts)}</text>')
    out.append("</svg>")
    open(OUT, "w").write("\n".join(out))
    print(f"wrote {OUT}: {COLS}x{ROWS}")

if __name__ == "__main__":
    main()
