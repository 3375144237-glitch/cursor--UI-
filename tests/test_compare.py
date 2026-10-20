import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.compare import align, diff_regions, similarity


def _page():
    img = np.full((900, 720, 3), 245, dtype=np.uint8)
    img[80:140, 40:680] = (40, 40, 40)      # 标题条
    img[200:260, 40:340] = (255, 140, 0)    # 按钮
    img[400:460, 40:680] = (220, 220, 220)
    return img


def test_identical_pages_have_no_regions():
    img = _page()
    _, regions = diff_regions(img, img.copy())
    assert regions == []
    assert similarity(img, img) == 1.0


def test_changed_button_is_located():
    design = _page()
    actual = _page()
    actual[200:260, 40:340] = (0, 120, 255)
    _, regions = diff_regions(design, actual)
    assert len(regions) == 1
    r = regions[0]
    assert r.kind == "changed"
    assert abs(r.x - 40) <= 6 and abs(r.y - 200) <= 6
    assert abs(r.w - 300) <= 10 and abs(r.h - 60) <= 10
    assert r.peak_diff > 100


def test_removed_element_is_marked_missing():
    design = _page()
    actual = _page()
    actual[200:260, 40:340] = 245  # 按钮被抹成背景
    _, regions = diff_regions(design, actual)
    assert len(regions) == 1
    assert regions[0].kind == "missing"


def test_ignore_rect_suppresses_region():
    design = _page()
    actual = _page()
    actual[200:260, 40:340] = (0, 120, 255)
    _, regions = diff_regions(design, actual, ignore=[(0, 180, 720, 100)])
    assert regions == []


def test_small_noise_below_min_area_is_ignored():
    design = _page()
    actual = _page()
    actual[10:12, 10:12] = (0, 0, 0)
    _, regions = diff_regions(design, actual)
    assert regions == []


def test_align_recovers_shift():
    rng = np.random.default_rng(7)
    design = rng.integers(0, 255, (300, 300, 3), dtype=np.uint8)
    import cv2

    actual = cv2.warpAffine(
        design, np.float32([[1, 0, 12], [0, 1, 5]]), (300, 300),
        borderMode=cv2.BORDER_REPLICATE,
    )
    fixed, (dx, dy) = align(design, actual)
    assert abs(dx - 12) <= 1 and abs(dy - 5) <= 1
    # 排除平移后需要填充的边界
    assert similarity(design[20:-20, 20:-20], fixed[20:-20, 20:-20]) > 0.99
