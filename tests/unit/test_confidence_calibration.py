import pytest
import numpy as np

from ai_engine.modules.confidence_calibration import TemperatureScaler, find_optimal_threshold_from_pr_curve


def test_temperature_scaling_calibration():
    # Khi model quá tự tin (overconfident), T > 1 sẽ kéo confidence về sát xác suất thực
    scaler = TemperatureScaler(temperature=1.5)
    raw_confs = np.array([0.90, 0.70, 0.50])
    calibrated = scaler.calibrate(raw_confs)

    # Các giá trị xác suất cao bị giảm nhẹ về đúng mức tin cậy
    assert calibrated[0] < raw_confs[0]
    assert calibrated[1] < raw_confs[1]
    assert calibrated[2] == pytest.approx(0.50, abs=0.01)


def test_optimal_threshold_from_pr_curve():
    # Tập dữ liệu kiểm chuẩn có nhãn
    confidences = np.array([0.95, 0.88, 0.75, 0.65, 0.55, 0.45, 0.35, 0.25, 0.15, 0.05])
    labels = np.array([1, 1, 1, 1, 1, 0, 0, 0, 0, 0])

    res = find_optimal_threshold_from_pr_curve(confidences, labels, target_metric="f1")
    assert res["optimal_threshold"] > 0.45
    assert res["f1_at_threshold"] == 1.0  # Tách biệt hoàn hảo tại ngưỡng ~ 0.50
