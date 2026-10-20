#!/usr/bin/env python3
"""单页走查：设计稿 + 实机截图 → 对比图 + Excel 问题表。

用法：
  .venv/bin/python check_ui.py --design 设计稿.png --device 实机.png \
      --model "iPhone 15 Pro" --page 首页 --mode A
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2

from src.compare import align, diff_regions, render, similarity, to_json
from src.device import design_scale, find_device
from src.normalize import normalize
from src.report import build_report, save_pair_image, stamp


def main() -> int:
    p = argparse.ArgumentParser(description="UI 走查比对")
    p.add_argument("--design", required=True, help="设计稿图片路径")
    p.add_argument("--device", required=True, help="手机截图路径")
    p.add_argument("--model", required=True, help="机型，如 'iPhone 15 Pro' 或 'Pixel 8'")
    p.add_argument("--page", default="页面", help="页面名称，写入报告")
    p.add_argument("--mode", choices=["A", "B"], default="A", help="A=整体等比缩放，B=固定尺寸适配")
    p.add_argument("--threshold", type=int, default=28, help="色差阈值 0-255，越小越敏感")
    p.add_argument("--status-bar", type=float, default=None, help="状态栏高度（点），默认按平台")
    p.add_argument("--no-align", action="store_true", help="跳过自动对齐")
    p.add_argument("--out", default="output", help="输出目录")
    args = p.parse_args()

    design = cv2.imread(args.design, cv2.IMREAD_COLOR)
    if design is None:
        print(f"无法读取设计稿：{args.design}", file=sys.stderr)
        return 1

    device_img = cv2.imread(args.device, cv2.IMREAD_COLOR)
    if device_img is None:
        print(f"无法读取截图：{args.device}", file=sys.stderr)
        return 1

    try:
        device = find_device(args.model, screenshot_width=device_img.shape[1])
    except ValueError as e:
        print(e, file=sys.stderr)
        return 1

    design_w = design.shape[1]
    if design_w != device_img.shape[1]:
        actual, norm_info = normalize(args.device, device, design_w, args.mode, args.status_bar)
    else:
        actual = cv2.resize(device_img, (design_w, int(device_img.shape[0] * design_w / device_img.shape[1])))
        norm_info = {"output": f"{actual.shape[1]}x{actual.shape[0]}", "mode": "screenshot"}

    offset = (0, 0)
    if not args.no_align:
        actual, offset = align(design, actual)

    delta, regions = diff_regions(design, actual, threshold=args.threshold)
    simil = similarity(design, actual)

    out = Path(args.out) / f"{stamp()}_{args.page}"
    out.mkdir(parents=True, exist_ok=True)
    design_w_pt = round(design_w / design_scale(design_w), 1)

    views = render(design, actual, delta, regions)
    for name, image in views.items():
        cv2.imwrite(str(out / f"{name}.png"), image)
    save_pair_image(design, actual, out / "compare.png")

    result = to_json(regions, simil, offset)
    result["page"] = args.page
    result["device"] = device.model
    result["design"] = f"{design_w}px / {design_w_pt}pt"
    result.update(norm_info)
    (out / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    report = build_report(args.page, design, actual, regions, out / f"{args.page}_问题表.xlsx")

    print(f"机型      {device.model}  ({device.point_w}x{device.point_h}pt, {device.scale}x)")
    print(f"归一化    {norm_info['output']}  模式 {norm_info['mode']}")
    print(f"设计稿    {design_w}px = {design_w_pt}pt")
    print(f"对齐偏移  dx={offset[0]}, dy={offset[1]}")
    print(f"相似度    {simil}")
    print(f"问题数量  {len(regions)}")
    for i, r in enumerate(regions, 1):
        print(f"  {i}. ({r.x},{r.y}) {r.w}x{r.h}  {r.kind}  峰值 {r.peak_diff}")
    print(f"输出目录  {out.resolve()}")
    print(f"问题表    {report.resolve()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
