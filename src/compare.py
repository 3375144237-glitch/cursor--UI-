"""设计稿与实机截图的差异检测。"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path

import cv2
import numpy as np
from skimage.metrics import structural_similarity


@dataclass
class Region:
    x: int
    y: int
    w: int
    h: int
    mean_diff: float
    peak_diff: float
    kind: str

    @property
    def area(self) -> int:
        return self.w * self.h


def align(design: np.ndarray, actual: np.ndarray, max_shift: int = 60) -> tuple[np.ndarray, tuple[int, int]]:
    """在 max_shift 像素范围内平移实机图，使它与设计稿最吻合。返回对齐后的图与偏移量。"""
    g1 = cv2.cvtColor(design, cv2.COLOR_BGR2GRAY).astype(np.float32)
    g2 = cv2.cvtColor(actual, cv2.COLOR_BGR2GRAY).astype(np.float32)
    h = min(g1.shape[0], g2.shape[0])
    w = min(g1.shape[1], g2.shape[1])
    g1, g2 = g1[:h, :w], g2[:h, :w]

    # 加窗的相位相关：对整幅图的平移估计比模板匹配稳健
    window = cv2.createHanningWindow((w, h), cv2.CV_32F)
    (sx, sy), response = cv2.phaseCorrelate(g1, g2, window)
    if response < 0.05 or abs(sx) > max_shift or abs(sy) > max_shift:
        return actual, (0, 0)

    dx, dy = int(round(sx)), int(round(sy))
    if dx == 0 and dy == 0:
        return actual, (0, 0)

    matrix = np.float32([[1, 0, -dx], [0, 1, -dy]])
    shifted = cv2.warpAffine(
        actual, matrix, (actual.shape[1], actual.shape[0]),
        flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE,
    )
    return shifted, (dx, dy)


def diff_regions(
    design: np.ndarray,
    actual: np.ndarray,
    threshold: int = 28,
    min_area: int = 400,
    ignore: list[tuple[int, int, int, int]] | None = None,
) -> tuple[np.ndarray, list[Region]]:
    """
    返回每个像素的最大通道差值（0-255）和差异区域。
    ignore: 忽略的矩形列表 [(x, y, w, h)]，例如状态栏、动态头像。
    """
    h = min(design.shape[0], actual.shape[0])
    w = min(design.shape[1], actual.shape[1])
    a = design[:h, :w].astype(np.int16)
    b = actual[:h, :w].astype(np.int16)

    delta = np.abs(a - b).max(axis=2).astype(np.uint8)
    mask = (delta > threshold).astype(np.uint8) * 255

    for x, y, rw, rh in ignore or []:
        mask[max(0, y):y + rh, max(0, x):x + rw] = 0

    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=8)
    regions: list[Region] = []
    for i in range(1, count):
        x, y, rw, rh, area = stats[i]
        if area < min_area:
            continue
        inside = delta[y:y + rh, x:x + rw]
        regions.append(Region(
            int(x), int(y), int(rw), int(rh),
            mean_diff=round(float(inside.mean()), 1),
            peak_diff=int(inside.max()),
            kind="missing" if _blank_side(b, x, y, rw, rh) else "changed",
        ))

    regions.sort(key=lambda r: r.area, reverse=True)
    return delta, regions


def _blank_side(image: np.ndarray, x: int, y: int, w: int, h: int) -> bool:
    """实机图该区域是否接近纯色背景（元素缺失）。"""
    patch = image[y:y + h, x:x + w]
    return patch.size > 0 and float(patch.std()) < 6


def similarity(design: np.ndarray, actual: np.ndarray) -> float:
    h = min(design.shape[0], actual.shape[0])
    w = min(design.shape[1], actual.shape[1])
    g1 = cv2.cvtColor(design[:h, :w], cv2.COLOR_BGR2GRAY)
    g2 = cv2.cvtColor(actual[:h, :w], cv2.COLOR_BGR2GRAY)
    return round(float(structural_similarity(g1, g2)), 4)


def render(
    design: np.ndarray,
    actual: np.ndarray,
    delta: np.ndarray,
    regions: list[Region],
) -> dict[str, np.ndarray]:
    """生成人工复核用图：并排图、叠加图、热力图。"""
    h = min(design.shape[0], actual.shape[0])
    w = min(design.shape[1], actual.shape[1])
    design, actual = design[:h, :w], actual[:h, :w]

    overlay = cv2.addWeighted(design, 0.5, actual, 0.5, 0)
    heat = cv2.applyColorMap(cv2.cvtColor(delta, cv2.COLOR_GRAY2BGR), cv2.COLORMAP_JET)

    drawn = actual.copy()
    for idx, r in enumerate(regions, 1):
        color = (0, 0, 255) if r.kind == "missing" else (0, 165, 255)
        cv2.rectangle(drawn, (r.x, r.y), (r.x + r.w, r.y + r.h), color, 3)
        cv2.putText(drawn, str(idx), (r.x + 6, r.y + 26),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2, cv2.LINE_AA)

    side = np.hstack([design, actual, drawn])
    return {"side_by_side": side, "overlay": overlay, "heatmap": heat, "marked": drawn}


def crop_pair(design: np.ndarray, actual: np.ndarray, r: Region, pad: int = 24) -> np.ndarray:
    """裁出单个问题的设计稿/实机对比小图。"""
    h, w = design.shape[:2]
    x0, y0 = max(0, r.x - pad), max(0, r.y - pad)
    x1, y1 = min(w, r.x + r.w + pad), min(h, r.y + r.h + pad)
    left = design[y0:y1, x0:x1]
    right = actual[y0:y1, x0:x1]
    return np.hstack([left, np.full((left.shape[0], 2, 3), 255, np.uint8), right])


def to_json(regions: list[Region], simil: float, shift: tuple[int, int]) -> dict:
    return {
        "similarity": simil,
        "shift": {"dx": shift[0], "dy": shift[1]},
        "count": len(regions),
        "regions": [asdict(r) for r in regions],
    }
