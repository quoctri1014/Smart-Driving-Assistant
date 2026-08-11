"""
utils.py
--------
Các hàm dùng chung: vẽ hộp/nhãn, chuyển toạ độ % -> pixel,
kiểm tra điểm nằm trong đa giác (dùng cho zone counting & collision).
"""

import cv2
import numpy as np
from shapely.geometry import Point, Polygon


def polygon_percent_to_pixels(polygon_percent, frame_width, frame_height):
    """Chuyển danh sách điểm (x%, y%) sang toạ độ pixel thực tế của khung hình."""
    return [(int(x * frame_width), int(y * frame_height)) for x, y in polygon_percent]


def point_in_polygon(point_xy, polygon_pixels):
    """Trả về True nếu điểm (x, y) nằm trong đa giác polygon_pixels."""
    return Polygon(polygon_pixels).contains(Point(point_xy))


def draw_polygon(frame, polygon_pixels, color, label=None, alpha=0.15):
    """Vẽ vùng (zone) bán trong suốt kèm nhãn lên khung hình."""
    overlay = frame.copy()
    pts = np.array(polygon_pixels, dtype=np.int32)
    cv2.fillPoly(overlay, [pts], color)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    cv2.polylines(frame, [pts], isClosed=True, color=color, thickness=2)
    if label:
        x, y = polygon_pixels[0]
        cv2.putText(frame, label, (x, y - 8), cv2.FONT_HERSHEY_SIMPLEX,
                    0.6, color, 2, cv2.LINE_AA)
    return frame


def draw_box(frame, box, color, label=None, thickness=2, font_scale=0.5):
    """Vẽ bounding box + nhãn."""
    x1, y1, x2, y2 = [int(v) for v in box]
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
    if label:
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 1)
        cv2.rectangle(frame, (x1, y1 - th - 8), (x1 + tw + 4, y1), color, -1)
        cv2.putText(frame, label, (x1 + 2, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX,
                    font_scale, (255, 255, 255), 1, cv2.LINE_AA)
    return frame


def box_center(box):
    x1, y1, x2, y2 = box
    return (int((x1 + x2) / 2), int((y1 + y2) / 2))


def box_bottom_center(box):
    """Điểm giữa đáy hộp - dùng để kiểm tra xe/người thuộc zone nào (điểm chạm đất)."""
    x1, y1, x2, y2 = box
    return (int((x1 + x2) / 2), int(y2))


def iou(boxA, boxB):
    """Intersection over Union giữa 2 bounding box, dùng cho tracking đơn giản."""
    xa1, ya1, xa2, ya2 = boxA
    xb1, yb1, xb2, yb2 = boxB
    inter_x1, inter_y1 = max(xa1, xb1), max(ya1, yb1)
    inter_x2, inter_y2 = min(xa2, xb2), min(ya2, yb2)
    inter_w, inter_h = max(0, inter_x2 - inter_x1), max(0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h
    areaA = max(0, xa2 - xa1) * max(0, ya2 - ya1)
    areaB = max(0, xb2 - xb1) * max(0, yb2 - yb1)
    union = areaA + areaB - inter_area
    return inter_area / union if union > 0 else 0
