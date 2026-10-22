#!/usr/bin/env python3
"""生成"设计稿 | 实机截图"并排图（带纵向刻度），分段输出，供人工/AI 走查与定位问题坐标。

PX 模式：设计稿左对齐放在与截图同宽的画布上，坐标以实机截图像素为准。
"""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

RULER = 56


def ruler(height: int, step: int = 50) -> np.ndarray:
    r = np.full((height, RULER, 3), 255, np.uint8)
    for y in range(0, height, step):
        major = y % 100 == 0
        cv2.line(r, (RULER - (18 if major else 8), y), (RULER, y), (0, 0, 220) if major else (150, 150, 150), 1)
        if major:
            cv2.putText(r, str(y), (2, y + 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 200), 1, cv2.LINE_AA)
    return r


def grid(img: np.ndarray, step: int = 100) -> np.ndarray:
    out = img.copy()
    for x in range(step, img.shape[1], step):
        out[:, x] = (out[:, x] * 0.6 + np.array([255, 120, 0]) * 0.4).astype(np.uint8)
        cv2.putText(out, str(x), (x + 2, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 80, 0), 1, cv2.LINE_AA)
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("design")
    p.add_argument("shot")
    p.add_argument("--out", default="/tmp/pair")
    p.add_argument("--chunk", type=int, default=600)
    p.add_argument("--design-offset", type=int, default=0, help="设计稿纵向起点（滚动截图用）")
    p.add_argument("--grid", action="store_true")
    a = p.parse_args()

    d = cv2.imread(a.design)[a.design_offset:]
    s = cv2.imread(a.shot)
    h, w = s.shape[:2]
    canvas = np.full((h, w, 3), 235, np.uint8)
    dh = min(h, d.shape[0])
    canvas[:dh, :d.shape[1]] = d[:dh]
    if a.grid:
        s = grid(s)
    gap = np.full((h, 12, 3), 120, np.uint8)
    full = np.hstack([ruler(h), canvas, gap, s, ruler(h)])

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for i, y in enumerate(range(0, h, a.chunk)):
        cv2.imwrite(str(out / f"part{i}.png"), full[y:y + a.chunk])
    print(f"{(h + a.chunk - 1) // a.chunk} 段 → {out}")


if __name__ == "__main__":
    main()
