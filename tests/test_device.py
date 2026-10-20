import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.device import design_scale, find_device
from src.normalize import normalize


def test_iphone_15_pro_known_spec():
    d = find_device("iPhone 15 Pro", screenshot_width=1179)
    assert (d.point_w, d.scale, d.platform) == (393, 3, "ios")


def test_iphone_model_width_mismatch_rejected():
    with pytest.raises(ValueError, match="截图宽度"):
        find_device("iPhone 15 Pro", screenshot_width=1290)


def test_android_by_model():
    d = find_device("Pixel 8", screenshot_width=1080)
    assert d.point_w == 412


def test_ambiguous_width_asks_for_model():
    with pytest.raises(ValueError, match="多个机型"):
        find_device("未知机型", screenshot_width=1080)


def test_unknown_device_raises():
    with pytest.raises(ValueError, match="未知机型"):
        find_device("Nokia 3310")


def test_design_scale_for_720():
    assert design_scale(720) == 2
    assert design_scale(750) == 2
    assert design_scale(1080) == 3
    assert design_scale(375) == 1


def test_normalize_mode_a_scales_whole_page():
    device = find_device("iPhone 15 Pro", screenshot_width=1179)
    screenshot = np.full((2556, 1179, 3), 255, dtype=np.uint8)
    out, info = normalize(_write(screenshot), device, design_width=720, mode="A")
    assert out.shape[1] == 720
    # 1179-59*3 行缩放 720/1179 后约等于 750 * 2379/1179
    assert info["output"] == f"720x{out.shape[0]}"
    assert abs(out.shape[0] - round(2379 * 720 / 1179)) <= 1


def test_normalize_mode_b_keeps_points():
    device = find_device("iPhone 15 Pro", screenshot_width=1179)
    screenshot = np.full((2556, 1179, 3), 255, dtype=np.uint8)
    # 2倍设计稿 / 3倍屏 = 2/3，360pt 页宽 -> 720px
    out, _ = normalize(_write(screenshot), device, design_width=720, mode="B")
    assert out.shape[1] == 720


def test_normalize_rejects_corrupt_file(tmp_path):
    bad = tmp_path / "bad.png"
    bad.write_bytes(b"not an image")
    device = find_device("iPhone 15 Pro", screenshot_width=1179)
    with pytest.raises(ValueError, match="无法读取"):
        normalize(bad, device, design_width=720)


def _write(image: np.ndarray) -> Path:
    import cv2
    import tempfile

    fd = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    cv2.imwrite(fd.name, image)
    return Path(fd.name)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
