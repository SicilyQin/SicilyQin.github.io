# -*- coding: utf-8 -*-
"""
为“图片墙”页面生成占位壁纸（SVG，无需 Pillow/字体）。
每张图 = 多层径向渐变 + 柔和光斑，风格统一、可直接当壁纸看。
用户以后拿到真图时，只要把 static/img/gallery/wall-*.svg 换成同名 .jpg 并改 图片.html 的后缀即可。
"""
import os
import math

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static', 'img', 'gallery')
OUT = os.path.abspath(OUT)
os.makedirs(OUT, exist_ok=True)

W, H = 1600, 1000

# (文件名, 深色底, 主色, 次色, 高光色)
PALETTES = [
    ('wall-01', '#0b1026', '#2b5bff', '#7b2ff7', '#00e5ff'),
    ('wall-02', '#1a0b1e', '#ff2e93', '#7b2ff7', '#ffd166'),
    ('wall-03', '#04121a', '#00b4d8', '#06d6a0', '#caf0f8'),
    ('wall-04', '#1b0f06', '#ff7b00', '#ff006e', '#ffe066'),
    ('wall-05', '#0a1408', '#38b000', '#9ef01a', '#d8f3dc'),
    ('wall-06', '#12061f', '#8e2de2', '#4a00e0', '#f72585'),
    ('wall-07', '#031926', '#468189', '#9dbebb', '#f4e9cd'),
    ('wall-08', '#1d0202', '#e01e37', '#ff9e00', '#ffd60a'),
    ('wall-09', '#050510', '#3a0ca3', '#4361ee', '#4cc9f0'),
]


def blobs(idx, main, second, accent):
    """生成 5 个随机感（但由 idx 决定，可复现）的光斑。"""
    out = []
    for i in range(5):
        a = (idx * 47 + i * 137) % 360
        r = 280 + ((idx * 31 + i * 61) % 5) * 90
        cx = 200 + int((math.cos(math.radians(a)) * 0.5 + 0.5) * (W - 400))
        cy = 150 + int((math.sin(math.radians(a)) * 0.5 + 0.5) * (H - 300))
        color = [main, second, accent][i % 3]
        op = 0.32 + ((idx + i) % 4) * 0.08
        out.append((cx, cy, r, color, round(op, 2)))
    return out


def svg(idx, base, main, second, accent, name):
    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}">'
    )
    parts.append(
        '<defs>'
        f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{base}"/>'
        f'<stop offset="1" stop-color="{main}" stop-opacity="0.25"/>'
        '</linearGradient>'
        '<filter id="soft" x="-50%" y="-50%" width="200%" height="200%">'
        '<feGaussianBlur stdDeviation="90"/></filter>'
        '<filter id="grain"><feTurbulence type="fractalNoise" baseFrequency="0.9" '
        'numOctaves="2" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/>'
        '<feComponentTransfer><feFuncA type="linear" slope="0.05"/></feComponentTransfer>'
        '</filter>'
        '</defs>'
    )
    parts.append(f'<rect width="{W}" height="{H}" fill="url(#bg)"/>')
    parts.append('<g filter="url(#soft)">')
    for cx, cy, r, color, op in blobs(idx, main, second, accent):
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" opacity="{op}"/>')
    parts.append('</g>')
    parts.append(f'<rect width="{W}" height="{H}" filter="url(#grain)" opacity="0.6"/>')
    parts.append(
        f'<rect x="40" y="40" width="{W-80}" height="{H-80}" fill="none" '
        f'stroke="#ffffff" stroke-opacity="0.10" stroke-width="2" rx="24"/>'
    )
    parts.append('</svg>')
    path = os.path.join(OUT, name + '.svg')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(parts))
    return path


for i, (name, base, main, second, accent) in enumerate(PALETTES):
    p = svg(i + 1, base, main, second, accent, name)
    print('wrote', p, os.path.getsize(p), 'bytes')
