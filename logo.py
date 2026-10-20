# -*- coding: utf-8 -*-
"""
logo.py - Logo LangScan: chu ky "Vinh" viet tay tren nen tre xanh.

Dung chung cho icon file .exe (build.py) va icon khay he thong (langscan.py).
Co nho (<= 40px, tren taskbar / khay) chu "Vinh" khong doc duoc nen chi ve
chu "V" cung kieu viet tay.

Xem thu:  python logo.py   -> build/logo_preview.png
"""

import os

GREEN = "#1f5f46"
BAMBOO = "#2a7a59"
NODE = "#195040"
INK = "#f6e7b0"
SMALL = 40                    # tu co nay tro xuong: chi ve chu V


def _font(size):
    from PIL import ImageFont
    fonts = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")
    for name in ("segoesc.ttf", "segoescb.ttf", "segoeuib.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(os.path.join(fonts, name), size)
        except Exception:
            continue
    return ImageFont.load_default()


def draw(size=256):
    """Ve logo o mot co (ve that o 4x roi thu nho cho min net)."""
    from PIL import Image, ImageDraw
    k = 4
    s = size * k
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    u = s / 256.0                                 # don vi theo khung 256
    d.rounded_rectangle([0, 0, s - 1, s - 1], radius=int(56 * u), fill=GREEN)

    small = size <= SMALL
    # Than tre: co lon 3 cay, co nho 2 cay mong cho do roi
    stalks = (34, 222) if small else (30, 70, 214)
    for x in stalks:
        w = 12 * u
        d.rectangle([x * u, 0, x * u + w, s], fill=BAMBOO)
        for y in (58, 138, 208):
            d.rectangle([x * u - 2 * u, y * u, x * u + w + 2 * u, y * u + 5 * u], fill=NODE)

    if small:
        d.text((s / 2 + 4 * u, s / 2 - 4 * u), "V", font=_font(int(200 * u)),
               fill=INK, anchor="mm")
        d.line([60 * u, 206 * u, 196 * u, 206 * u], fill=INK, width=int(14 * u))
    else:
        d.text((132 * u, 116 * u), "Vinh", font=_font(int(78 * u)), fill=INK, anchor="mm")
        # net gach duoi kieu chu ky, hoi cong o dau
        d.line([58 * u, 170 * u, 204 * u, 166 * u], fill=INK, width=int(5 * u))
        d.line([204 * u, 166 * u, 214 * u, 156 * u], fill=INK, width=int(5 * u))
    return img.resize((size, size), Image.LANCZOS)


ICO_SIZES = (16, 24, 32, 48, 64, 128, 256)


def save_ico(path):
    """File .ico chua anh rieng cho tung co (co nho la chu V)."""
    imgs = [draw(n) for n in ICO_SIZES]
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    imgs[-1].save(path, format="ICO", sizes=[(n, n) for n in ICO_SIZES],
                  append_images=imgs[:-1])


def main():
    from PIL import Image
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build",
                       "logo_preview.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sheet = Image.new("RGBA", (256 + 20 + 64 + 20 + 32 + 20 + 16 + 20, 276), "#f4f4f6")
    x = 10
    for n in (256, 64, 32, 16):
        im = draw(n)
        sheet.paste(im, (x, 10), im)
        x += n + 20
    sheet.save(out)
    print(out)


if __name__ == "__main__":
    main()
