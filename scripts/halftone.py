#!/usr/bin/env python3
"""Gera imagens em halftone de pontos — tema Cyberpunk: Edgerunners.

Lê cada imagem de assets/src/ e salva assets/<nome>.png com:
  - halftone de pontos em grade rotacionada 45° (área do ponto ∝ tom)
  - pontos na cor de --color, fundo transparente
  - borda branca irregular de "papel rasgado" em volta da silhueta
    (só o contorno é branco; dentro da figura ficam apenas os pontos)

A silhueta vem do canal alfa (PNG já recortado). Se a imagem não tiver
transparência, o fundo é detectado pela cor das bordas e removido.

uso:
  pip install -r scripts/requirements.txt
  python3 scripts/halftone.py
  python3 scripts/halftone.py --color "#FF003C" --size 240 --dot 4

opções:
  --color  cor dos pontos (padrão #FCEE09)
  --size   largura final em px, já contando a borda (padrão 400)
  --dot    espaçamento da grade em px (padrão 5)
"""
import argparse
import os
import zlib

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'assets', 'src')
OUT = os.path.join(HERE, '..', 'assets')
EXTS = ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp')

SS = 4        # supersampling dos pontos (antialias)
BG_TOL = 40   # tolerância RGB pra detectar o fundo quando não há alfa


def hex_rgb(s):
    h = s.lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    if len(h) != 6:
        raise argparse.ArgumentTypeError(f'cor inválida: {s}')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def to_img(a):
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


def to_arr(img):
    return np.asarray(img, np.float32) / 255


def silhouette(img):
    """Máscara da figura: usa o alfa; sem alfa, remove o fundo por flood fill a partir das bordas."""
    a = np.asarray(img)[..., 3]
    if a.min() < 128:
        return a >= 128
    rgb = np.asarray(img)[..., :3].astype(np.int16)
    edge = np.concatenate([rgb[0], rgb[-1], rgb[:, 0], rgb[:, -1]])
    near = np.abs(rgb - np.median(edge, axis=0)).max(axis=2) <= BG_TOL
    fill = Image.fromarray(np.where(near, 255, 0).astype(np.uint8))
    h, w = near.shape
    border = [(x, y) for x in range(w) for y in (0, h - 1)] + \
             [(x, y) for y in range(h) for x in (0, w - 1)]
    for xy in border:
        if fill.getpixel(xy) == 255:
            ImageDraw.floodfill(fill, xy, 128)
    mask = np.asarray(fill) != 128
    return mask if mask.any() else np.ones_like(mask)


def halftone(gray, mask, dot):
    """Alfa dos pontos (0..1). gray: 0 = preto, 1 = branco."""
    h, w = gray.shape
    ys, xs = np.mgrid[0:h * SS, 0:w * SS].astype(np.float32)
    xs, ys = (xs + .5) / SS, (ys + .5) / SS
    k = np.float32(np.sqrt(.5))
    u, v = (xs + ys) * k, (ys - xs) * k               # coords na grade girada 45°
    uc, vc = np.round(u / dot) * dot, np.round(v / dot) * dot
    cx, cy = (uc - vc) * k, (uc + vc) * k             # centro do ponto em xy
    inside = (cx >= 0) & (cx < w) & (cy >= 0) & (cy < h)
    ix = np.clip(cx, 0, w - 1).astype(np.int32)
    iy = np.clip(cy, 0, h - 1).astype(np.int32)
    ink = (1 - gray[iy, ix]) * (mask[iy, ix] & inside)
    r2 = dot * dot * ink / np.pi                       # área do ponto = ink * dot²
    on = (xs - cx) ** 2 + (ys - cy) ** 2 <= r2
    return on.reshape(h, SS, w, SS).mean(axis=(1, 3))


def torn_paper(mask, border, rng):
    """Alfa do papel: silhueta dilatada com a beirada deformada por ruído."""
    h, w = mask.shape
    m = to_img(mask.astype(np.float32)).filter(ImageFilter.MaxFilter(border * 2 + 1))
    field = to_arr(m.filter(ImageFilter.GaussianBlur(border / 3)))
    # ruído em duas escalas: ondulação larga do rasgo + fibra miúda do papel
    lo = rng.random((max(h // 24, 2), max(w // 24, 2)))
    lo = to_arr(to_img(lo).resize((w, h), Image.Resampling.BICUBIC))
    hi = to_arr(to_img(rng.random((h, w))).filter(ImageFilter.GaussianBlur(1)))
    paper = (field + (lo - .5) * .9 + (hi - .5) * .6 > .5) | mask
    return to_arr(to_img(paper.astype(np.float32)).filter(ImageFilter.GaussianBlur(.7)))


def process(path, color, size, dot):
    name = os.path.splitext(os.path.basename(path))[0]
    img = Image.open(path)
    img.seek(0)
    img = img.convert('RGBA')

    border = max(dot * 2, size // 40)
    pad = border * 2
    inner = size - 2 * pad
    if inner < dot * 4:
        raise SystemExit(f'--size {size} pequeno demais pra --dot {dot}')
    img = img.resize((inner, max(1, round(img.height * inner / img.width))),
                     Image.Resampling.LANCZOS)

    mask0 = silhouette(img)
    flat = Image.new('RGBA', img.size, 'white')
    flat.alpha_composite(img)
    gray = ImageOps.autocontrast(flat.convert('L'), cutoff=1,
                                 mask=to_img(mask0.astype(np.float32)))
    gray = to_arr(gray.filter(ImageFilter.GaussianBlur(dot / 3)))

    mask = np.pad(mask0, pad)
    gray = np.pad(gray, pad, constant_values=1)
    rng = np.random.default_rng(zlib.crc32(name.encode()))

    soft = to_arr(to_img(mask.astype(np.float32)).filter(ImageFilter.GaussianBlur(.7)))
    ring = torn_paper(mask, border, rng) * (1 - soft)
    ink = halftone(gray, mask, dot)

    # ponto por cima do papel (operador "over")
    alpha = ink + ring * (1 - ink)
    col = np.array(color, np.float32)
    rgb = (col * ink[..., None] + 255 * (ring * (1 - ink))[..., None]) / np.maximum(alpha, 1e-6)[..., None]
    out = np.dstack([rgb, alpha * 255]).round().clip(0, 255).astype(np.uint8)

    dst = os.path.join(OUT, f'{name}.png')
    Image.fromarray(out, 'RGBA').save(dst, optimize=True)
    print(f'ok {name}.png {out.shape[1]}x{out.shape[0]}')


def main():
    ap = argparse.ArgumentParser(description='halftone edgerunners: assets/src/* → assets/*.png')
    ap.add_argument('--color', type=hex_rgb, default='#FCEE09', help='cor dos pontos (padrão #FCEE09)')
    ap.add_argument('--size', type=int, default=400, help='largura final em px (padrão 400)')
    ap.add_argument('--dot', type=int, default=5, help='espaçamento da grade em px (padrão 5)')
    args = ap.parse_args()
    if args.dot < 2:
        ap.error('--dot precisa ser >= 2')

    files = sorted(f for f in os.listdir(SRC) if f.lower().endswith(EXTS)) if os.path.isdir(SRC) else []
    if not files:
        print('nada em assets/src/ — coloque as imagens lá')
        return
    for f in files:
        process(os.path.join(SRC, f), args.color, args.size, args.dot)


if __name__ == '__main__':
    main()
