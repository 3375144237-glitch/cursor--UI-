"""在实机截图上用编号框标出问题位置。"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT_PATHS = [
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
]
COLORS = ["#FF3B30", "#FF9500", "#AF52DE", "#007AFF", "#34C759", "#FF2D55"]


def font(size: int) -> ImageFont.FreeTypeFont:
    for p in FONT_PATHS:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def color(index: int) -> str:
    return COLORS[(index - 1) % len(COLORS)]


def annotate(shot: Image.Image, boxes: list[list[int]], line: int = 6, badge: int = 30) -> Image.Image:
    """boxes 依次编号 1、2、3……；编号圆标放在框左上角外侧，避免遮挡问题内容。"""
    img = shot.convert("RGB").copy()
    draw = ImageDraw.Draw(img)
    f = font(int(badge * 1.2))
    W, H = img.size
    for i, (x, y, w, h) in enumerate(boxes, 1):
        c = color(i)
        draw.rounded_rectangle([x, y, x + w, y + h], radius=12, outline=c, width=line)
        cx = min(max(x, badge + 2), W - badge - 2)
        cy = min(max(y, badge + 2), H - badge - 2)
        draw.ellipse([cx - badge, cy - badge, cx + badge, cy + badge], fill=c, outline="white", width=4)
        draw.text((cx, cy), str(i), font=f, fill="white", anchor="mm")
    return img


def crop_pair(design: Image.Image, shot: Image.Image, box: list[int], index: int, pad: int = 40,
              design_offset: tuple[int, int] = (0, 0)) -> Image.Image:
    """单个问题的"设计稿 | 实机"局部对比图。design_offset 是实机坐标换算到设计稿坐标的偏移。"""
    x, y, w, h = box
    dx, dy = design_offset
    sx0, sy0 = max(0, x - pad), max(0, y - pad)
    sx1, sy1 = min(shot.width, x + w + pad), min(shot.height, y + h + pad)
    actual = shot.convert("RGB").crop((sx0, sy0, sx1, sy1))
    dx0, dy0 = max(0, sx0 + dx), max(0, sy0 + dy)
    ref = design.convert("RGB").crop((dx0, dy0, dx0 + (sx1 - sx0), dy0 + (sy1 - sy0)))

    label_h = 44
    gap = 12
    out = Image.new("RGB", (ref.width + actual.width + gap, max(ref.height, actual.height) + label_h), "white")
    out.paste(ref, (0, label_h))
    out.paste(actual, (ref.width + gap, label_h))
    d = ImageDraw.Draw(out)
    f = font(26)
    d.text((6, 8), "设计稿", font=f, fill="#333333")
    d.text((ref.width + gap + 6, 8), f"实机 · 问题{index}", font=f, fill=color(index))
    d.rectangle([ref.width + gap + (x - sx0), label_h + (y - sy0),
                 ref.width + gap + (x - sx0) + w, label_h + (y - sy0) + h], outline=color(index), width=3)
    return out
