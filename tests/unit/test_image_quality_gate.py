import pytest
import numpy as np
import cv2

from ai_engine.modules.image_quality_gate import ImageQualityGate, QualityReport


def test_quality_gate_sharp_image():
    gate = ImageQualityGate()
    # Tạo ảnh sắc nét có nhiều cạnh và hoa văn
    sharp_img = np.zeros((480, 640, 3), dtype=np.uint8)
    for i in range(0, 640, 20):
        cv2.line(sharp_img, (i, 0), (i, 480), (255, 255, 255), 2)
    for j in range(0, 480, 20):
        cv2.line(sharp_img, (0, j), (640, j), (200, 200, 200), 2)

    report, processed = gate.assess_frame(sharp_img)
    assert report.score >= 0.70
    assert not report.is_low_quality
    assert report.blur_score > 65.0


def test_quality_gate_blurred_image():
    gate = ImageQualityGate()
    # Tạo ảnh mờ mịn hoàn toàn (Gaussian blur lớn)
    base = np.random.randint(50, 200, (480, 640, 3), dtype=np.uint8)
    blurred_img = cv2.GaussianBlur(base, (51, 51), 0)

    report, processed = gate.assess_frame(blurred_img)
    assert report.is_low_quality
    assert any("mờ" in issue.lower() for issue in report.issues)


def test_quality_gate_dark_image_clahe_enhancement():
    gate = ImageQualityGate()
    # Tạo ảnh rất tối (mean < 35)
    dark_img = np.full((480, 640, 3), 20, dtype=np.uint8)
    # Thêm một ít kết cấu yếu
    cv2.rectangle(dark_img, (200, 200), (400, 400), (45, 45, 45), -1)

    report, processed = gate.assess_frame(dark_img)
    assert any("thiếu sáng" in issue.lower() for issue in report.issues)
    # Kiểm tra tiền xử lý CLAHE được kích hoạt
    assert report.enhanced is True


def test_quality_gate_glare_detection():
    gate = ImageQualityGate()
    # Tạo ảnh có vùng lóa sáng cực mạnh (đèn pha / ngược nắng chiếm > 15% diện tích)
    glare_img = np.full((480, 640, 3), 100, dtype=np.uint8)
    cv2.circle(glare_img, (320, 240), 160, (255, 255, 255), -1)

    report, processed = gate.assess_frame(glare_img)
    assert report.glare_ratio > 0.12
    assert any("chói" in issue.lower() or "lóa" in issue.lower() for issue in report.issues)
