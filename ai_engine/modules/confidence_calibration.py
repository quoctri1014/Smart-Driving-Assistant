"""
confidence_calibration.py
-------------------------
0.2 Hiệu chỉnh độ tin cậy (Confidence Calibration):
- Temperature Scaling: Chuẩn hóa xác suất đầu ra để phản ánh xác suất đúng thật.
- Tìm ngưỡng tối ưu từ đường cong Precision-Recall trên tập validation thực tế (thay vì chọn tay).
"""

from typing import List, Tuple, Dict, Any
import numpy as np


class TemperatureScaler:
    def __init__(self, temperature: float = 1.0):
        self.temperature = max(0.01, float(temperature))

    def calibrate(self, confidences: np.ndarray) -> np.ndarray:
        """
        Áp dụng scaling nhiệt độ:
        p -> logit z = ln(p / (1-p)) -> z / T -> p_cal = 1 / (1 + exp(-z/T))
        """
        confidences = np.clip(confidences, 1e-6, 1.0 - 1e-6)
        logits = np.log(confidences / (1.0 - confidences))
        scaled_logits = logits / self.temperature
        calibrated_probs = 1.0 / (1.0 + np.exp(-scaled_logits))
        return calibrated_probs

    def fit(self, confidences: np.ndarray, labels: np.ndarray, lr: float = 0.05, max_iters: int = 100) -> float:
        """
        Tối ưu hóa nhiệt độ T bằng cách cực tiểu hóa Negative Log-Likelihood (NLL)
        trên tập dữ liệu kiểm chuẩn có nhãn.
        """
        confidences = np.clip(np.array(confidences, dtype=np.float64), 1e-6, 1.0 - 1e-6)
        labels = np.array(labels, dtype=np.float64)
        logits = np.log(confidences / (1.0 - confidences))

        temp = self.temperature
        for _ in range(max_iters):
            scaled_logits = logits / temp
            probs = 1.0 / (1.0 + np.exp(-scaled_logits))
            
            # Đạo hàm của NLL theo temperature T
            # d_loss / d_T = sum( (probs - labels) * (-logits / T^2) )
            grad = np.mean((probs - labels) * (-logits / (temp ** 2)))
            temp -= lr * grad
            temp = max(0.1, min(5.0, temp))

        self.temperature = round(float(temp), 3)
        return self.temperature


def find_optimal_threshold_from_pr_curve(
    confidences: np.ndarray,
    labels: np.ndarray,
    target_metric: str = "f1",
    min_precision: float = 0.85
) -> Dict[str, Any]:
    """
    Xác định ngưỡng tin cậy tối ưu từ đường cong Precision-Recall, KHÔNG chọn tay:
    - Nếu target_metric == 'f1': Tìm ngưỡng đạt F1-score cao nhất.
    - Nếu target_metric == 'precision': Tìm ngưỡng thấp nhất thỏa mãn min_precision.
    """
    confidences = np.array(confidences)
    labels = np.array(labels)

    thresholds = np.linspace(0.05, 0.95, 91)
    best_thresh = 0.50
    best_score = 0.0
    best_p = 0.0
    best_r = 0.0

    for th in thresholds:
        preds = (confidences >= th).astype(int)
        tp = np.sum((preds == 1) & (labels == 1))
        fp = np.sum((preds == 1) & (labels == 0))
        fn = np.sum((preds == 0) & (labels == 1))

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        if target_metric == "f1":
            if f1 > best_score:
                best_score = f1
                best_thresh = th
                best_p = precision
                best_r = recall
        elif target_metric == "precision":
            if precision >= min_precision and recall > best_r:
                best_thresh = th
                best_score = precision
                best_p = precision
                best_r = recall

    return {
        "optimal_threshold": round(float(best_thresh), 3),
        "precision_at_threshold": round(float(best_p), 3),
        "recall_at_threshold": round(float(best_r), 3),
        "f1_at_threshold": round(float(best_score), 3)
    }
