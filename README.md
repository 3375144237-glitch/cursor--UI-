# UI 走查工具

把"设计稿 ↔ 真机截图"的比对从手工流程变成半自动：截图归一化 → 自动对齐 → 差异定位 → 生成带对比图的 Excel 问题表。人工只负责确认。

## 能做什么

- 按机型把手机截图换算到设计稿尺寸（支持整体等比 / 固定尺寸两种适配方式）
- 自动裁状态栏、对齐截图、定位差异区域
- 每处差异自动裁剪"设计稿 vs 实机"对比图，嵌入 Excel
- 输出相似度、偏移量等数据到 `result.json`，便于复核和留档

## 不能做什么

- 交互、动效、页面状态无法检查
- 系统字体渲染差异、阴影、1–2px 细节可能误报，需要人工确认
- 文案/图片内容不同属于正常，需要靠忽略区域或人工过滤

## 环境准备

```bash
python3 -m venv .venv
.venv/bin/pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
.venv/bin/pip install pytest
```

## 使用

```bash
.venv/bin/python check_ui.py \
  --design screenshots/design/首页.png \
  --device screenshots/device/首页_iPhone15Pro.png \
  --model "iPhone 15 Pro" \
  --page 首页 \
  --mode PX
```

参数：

| 参数 | 说明 |
|---|---|
| `--model` | 机型名，见 `config/device_profiles.yaml` |
| `--mode REM` | 等比缩放到设计稿宽度（如 720px） |
| `--mode PX` | 缩放到设备自身的 2 倍图（如 iPhone XR 828px、iPhone 15 Pro 786px），截图已是 2 倍图则不缩放 |
| `--threshold` | 色差阈值，默认 28；越小越敏感、误报越多 |
| `--status-bar` | 状态栏高度（点），默认 iOS 59 / 安卓 24 |
| `--no-align` | 跳过自动对齐 |

截图要求：原图（AirDrop 或微信原图），手机保持默认显示与字体大小。

## 输出

`output/日期_页面名/` 下：

- `compare.png` 设计稿与实机并排图
- `marked.png` 标出问题区域的实机图
- `overlay.png` 半透明叠加图
- `heatmap.png` 差异热力图
- `result.json` 问题区域坐标、相似度、对齐偏移
- `页面名_问题表.xlsx` 带对比小图的问题表（含"确认"列供人工勾选）

## 测试

```bash
.venv/bin/python -m pytest tests -q
```

## 目录

```
check_ui.py              命令行入口
src/device.py            机型 → 点尺寸换算
src/normalize.py         裁状态栏、缩放归一化
src/compare.py           对齐、差异检测、对比图
src/report.py            Excel 报告
config/device_profiles.yaml  机型规格表（可补充自己的测试机）
```
