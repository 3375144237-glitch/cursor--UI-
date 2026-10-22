# UI 走查工具交接文档

更新时间：2026-10-22　当前项目：麦奇说（iPhone XR，PX 实现）

## 1. 这是什么

把"设备截图 → 缩放 → 与设计稿比对 → 截图标注 → 填问题表"这套人工流程半自动化。工具负责缩放、并排对比、标注截图和生成 Excel，问题判断仍由人（或 AI 看图）确认后写进走查记录。

## 2. 缩放规则（以此为准）

| 实现方式 | 处理 |
|---|---|
| REM | 截图等比缩放到设计稿宽度 720px |
| PX | 截图缩放到设备自身的 2 倍图（宽 = 设备点宽 × 2），不一定是 720 |
| 截图本身就是 2 倍图 | 不缩放（会提前说明） |

实现方式、机型、截图是否为 2 倍图，会在给截图之前说明。设计稿本身是 2 倍图（720 宽）。

机型规格在 `config/device_profiles.yaml`，缺机型时在这里补。

## 3. PX 模式下怎么比对

PX 实现时，设备比设计稿宽多少，页面就"撑开"多少（XR 为 828 − 720 = 108px）：

- 边距、字号、高度、圆角应与设计稿相等
- 通栏卡片宽度 = 设计宽度 + 108
- 右对齐元素整体右移 108，居中元素右移 54
- XR 状态栏比设计稿高 12px，内容整体下移 12px，不算问题

所以 PX 模式不能整页叠图做像素比对（误报过半），要逐元素核对。REM 模式可以用 `check_ui.py` 整页比对。

不算问题的差异：状态栏内容、文案数据（数字、日期）、插画/头像内容、iPhone 截图色彩空间带来的轻微色差（如 #A1D64F → #A9DD66）。

## 4. 目录与脚本

| 路径 | 作用 |
|---|---|
| `check_ui.py` | 整页比对（REM 模式适用），输出差异图与报告 |
| `make_report.py` | 读走查记录，生成标注截图、局部对比图、问题表 Excel |
| `tools/pair_view.py` | 生成"设计稿 \| 实机"并排图（带刻度、可分段），用来定位问题坐标 |
| `src/normalize.py` | 状态栏裁剪、REM/PX 缩放 |
| `src/device.py` | 机型查询 |
| `src/compare.py` / `src/report.py` | 整页差异检测与旧版报告 |
| `src/annotate.py` | 编号彩色框标注、局部对比图裁剪 |
| `config/projects/maiqi.yaml` | 麦奇说截图 ↔ Figma 画板对应表 |
| `reviews/maiqi/issues.yaml` | 麦奇说走查记录（问题来源） |
| `tests/` | 17 个单测，`.venv/bin/python -m pytest tests -q` |

## 5. 走查一个页面的步骤

1. 在 `config/projects/maiqi.yaml` 确认截图对应的画板 node。
2. 生成并排图定位问题：
   ```bash
   .venv/bin/python tools/pair_view.py screenshots/design/maiqi/<画板>.png "<截图路径>" --out /tmp/pXXXX --chunk 900 --grid
   ```
3. 把问题写进 `reviews/maiqi/issues.yaml`：
   - `box`：问题在实机截图上的 `[x, y, 宽, 高]`
   - `design_offset`：实机坐标换算到设计稿的偏移，默认 `[0, -12]`；右对齐元素用 `[-108, -12]`
   - `desc` / `priority`（高/中/低）/ `status` / `note`
4. 生成问题表：
   ```bash
   .venv/bin/python make_report.py reviews/maiqi/issues.yaml
   ```
   输出在 `output/<项目>_<日期>/`：问题表 xlsx、`标注截图/`、`问题对比/`。

## 6. 问题表格式

沿用团队模板：设备 | 截图 | 问题描述 | 优先级 | 修复状态 | 备注。

- 同一页面多个问题："设备""截图"两列合并；截图上用 ①②③ 彩色框标位置，问题描述前带同一编号。
- 优先级、修复状态为下拉选择。
- 第二个工作表"问题对比图"：每个问题一张"设计稿 | 实机"局部图。

## 7. 当前进度

- 已完成：首页-单词运用（IMG_1297），4 个问题，已写入 `reviews/maiqi/issues.yaml`。
- 进行中：弹窗类页面（IMG_1314 / 1353 / 1347 / 1309）已出并排图，问题尚未记录。
- 未开始：其余页面。
- 撤回：此前"卡片圆角偏大到 40px"的判断，复测两边均约 30px，一致。

## 8. 待办与阻塞

1. **截图文件夹丢失**：`~/Desktop/麦奇说验收（测试-手机截图）` 已不存在，需要放回或更新 `config/projects/maiqi.yaml` 和 `reviews/maiqi/issues.yaml` 里的 `screenshot_dir`。
2. **页面对应关系待确认**：表中全部为"待确认"，重点是 IMG_1300、IMG_1302（开始/结束 还是 联赛页），以及 `675 1.png`（900×1413，非 XR 截图，暂排除）。IMG_1368 为"加载异常"页，无设计稿。
3. **问题表是否入库**：`output/` 被 `.gitignore` 忽略，问题表目前只在本地。

## 9. 注意事项

- **设计稿图片不在仓库里**（`screenshots/design/` 被忽略）。之前通过 Figma MCP 按画板导出到 `screenshots/design/maiqi/`，`index.json` 记录 node → 文件名。换机器需要重新导出，Figma 文件 key：`kYoNWHRIkZk9M2XM0gheNH`。
- `make_report.py` 里设计稿目录写死为 `screenshots/design/maiqi`，做其他项目时需要改成按项目读取。
- 截图请用原图（AirDrop 或微信原图），手机保持默认显示和字体大小。
- 自动按相似度配对页面不可靠（分数都在 0.75–0.85），目前靠人工配对。截图按页面名命名可以省掉这一步。
- `work/`（Lottie 动效分析，约 79MB）和 `tools/check_animation.py` 不属于 UI 走查，未提交。
