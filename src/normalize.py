"""截图归一化：裁状态栏、按适配方式缩放到设计稿宽度。"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from .device import Device, design_scale

# 状态栏高度（点）。各机型有差异，可在命令行覆盖。
STATUS_BAR_PT = {"ios": 59, "android": 24}


def crop_status_bar(image: np.ndarray, device: Device, height_pt: Optional[float] = None) -> np.ndarray:
    height_pt = STATUS_BAR_PT[device.platform] if height_pt is None else height_pt
    cut = int(round(height_pt * device.scale))
    return image[cut:, :]


def resize_to_design(
    image: np.ndarray,
    device: Device,
    design_width: int,
    mode: str = "A",
) -> np.ndarray:
    """
    mode A: 等比适配，整页按屏幕宽度缩放（间距字号随屏幕变化）。
    mode B: 固定尺寸适配，字号间距按设计值不变，只有通栏元素被拉伸。
    """
    if mode == "A":
        factor = design_width / image.shape[1]
    elif mode == "B":
        factor = design_scale(design_width) / device.scale
    else:
        raise ValueError("mode 只能是 A 或 B")

    height = int(round(image.shape[0] * factor))
    return cv2.resize(image, (design_width, height), interpolation=cv2.INTER_AREA)


def normalize(
    screenshot: str | Path,
    device: Device,
    design_width: int,
    mode: str = "A",
    status_bar_pt: Optional[float] = None,
) -> tuple[np.ndarray, dict]:
    image = cv2.imread(str(screenshot), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"无法读取图片：{screenshot}")

    cropped = crop_status_bar(image, device, status_bar_pt)
    result = resize_to_design(cropped, device, design_width, mode)
    info = {
        "screenshot": f"{image.shape[1]}x{image.shape[0]}",
        "device": device.model,
        "scale": device.scale,
        "mode": mode,
        "design_width": design_width,
        "design_bytes": [round(design_width / design_scale(design_width), 1), design_scale(design_width)],
        "output": f"{result.shape[1]}x{result.shape[0]}",
    }
    return result, info
