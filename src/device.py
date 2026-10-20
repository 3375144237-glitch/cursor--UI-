"""设备规格解析：把截图宽度和机型映射成 点(pt/dp) 尺寸。"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

PROFILES = Path(__file__).resolve().parent.parent / "config" / "device_profiles.yaml"


@dataclass
class Device:
    model: str
    platform: str
    width: int
    height: int
    point_w: float
    point_h: float
    scale: float


def _parse_point(value: str) -> tuple[float, float]:
    w, h = value.lower().split("x")
    return float(w), float(h)


def load_profiles(path: Path = PROFILES) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def find_device(model: str, screenshot_width: Optional[int] = None, path: Path = PROFILES) -> Device:
    """按机型名查找；找不到时用截图宽度在全部规格里反查。"""
    data = load_profiles(path)
    needle = model.strip().lower()

    for platform, entries in data.items():
        for name, spec in entries.items():
            if name.lower() == needle:
                if screenshot_width and spec["width"] != screenshot_width:
                    raise ValueError(
                        f"{name} 截图宽度应为 {spec['width']}px，实际是 {screenshot_width}px。"
                        "请确认机型或原始截图是否被压缩。"
                    )
                return _build(name, platform, spec)

    if screenshot_width:
        candidates = [
            (name, platform, spec)
            for platform, entries in data.items()
            for name, spec in entries.items()
            if spec["width"] == screenshot_width
        ]
        if len(candidates) == 1:
            return _build(*candidates[0])
        if len(candidates) > 1:
            names = "、".join(c[0] for c in candidates)
            raise ValueError(f"宽度 {screenshot_width}px 对应多个机型（{names}），请提供机型名。")

    raise ValueError(f"未知机型：{model}。请在 config/device_profiles.yaml 里补充规格。")


def _build(name: str, platform: str, spec: dict) -> Device:
    point_w, point_h = _parse_point(spec["point"])
    return Device(name, platform, spec["width"], spec["height"], point_w, point_h, float(spec["scale"]))


def design_scale(design_width: int) -> int:
    """设计稿按几倍图绘制：换算出的逻辑宽度落在 320~480 之间即为有效倍数。"""
    for factor in (2, 3, 4):
        if design_width % factor == 0 and 320 <= design_width // factor <= 480:
            return factor
    if 320 <= design_width <= 480:
        return 1
    raise ValueError(f"设计稿宽度 {design_width}px 无法推断倍数，请在配置里手动指定。")
