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


MODES = {"REM": "REM", "A": "REM", "PX": "PX", "B": "PX"}


def resize_to_design(
    image: np.ndarray,
    device: Device,
    design_width: int,
    mode: str = "REM",
) -> np.ndarray:
    """
    REM：整页等比缩放到设计稿宽度（如 720px）。
    PX ：按设备自身分辨率缩放到该设备的 2 倍图（宽 = 设备点宽 × 设计稿倍数），
         例如 iPhone XR 414pt → 828px，iPhone 15 Pro 393pt → 786px。
         截图本身已是 2 倍图时不缩放。
    """
    mode = MODES.get(mode.upper())
    if mode == "REM":
        factor = design_width / image.shape[1]
    elif mode == "PX":
        factor = design_scale(design_width) / device.scale
    else:
        raise ValueError("mode 只能是 REM 或 PX")

    if abs(factor - 1) < 1e-6:
        return image
    width = int(round(image.shape[1] * factor))
    height = int(round(image.shape[0] * factor))
    interp = cv2.INTER_AREA if factor < 1 else cv2.INTER_CUBIC
    return cv2.resize(image, (width, height), interpolation=interp)


def normalize(
    screenshot: str | Path,
    device: Device,
    design_width: int,
    mode: str = "REM",
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
