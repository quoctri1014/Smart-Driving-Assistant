import base64
import os
import re
import sys
import time
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parents[3]
MODEL_PATH = BASE_DIR / "web-app" / "public" / "models" / "sign.onnx"

router = APIRouter()

SIGN_CLASSES_58 = [
    'DP.135', 'P.102', 'P.103a', 'P.103b', 'P.103c', 'P.104', 'P.106a', 'P.106b', 'P.107a', 'P.112',
    'P.115', 'P.117', 'P.123a', 'P.123b', 'P.124a', 'P.124b', 'P.124c', 'P.125', 'P.127', 'P.128',
    'P.130', 'P.131a', 'P.137', 'P.245a', 'R.301c', 'R.301d', 'R.301e', 'R.302a', 'R.302b', 'R.303',
    'R.407a', 'R.409', 'R.425', 'R.434', 'S.509a', 'W.201a', 'W.201b', 'W.202a', 'W.202b', 'W.203b',
    'W.203c', 'W.205a', 'W.205b', 'W.205d', 'W.207a', 'W.207b', 'W.207c', 'W.208', 'W.209', 'W.210',
    'W.219', 'W.221b', 'W.224', 'W.225', 'W.227', 'W.233', 'W.235', 'W.245a'
]

VN_SIGN_INFO = {
    # 1. BIỂN BÁO CẤM (Nhóm P & DP) - QCVN 41:2019/BGTVT
    "DP.135": {"name": "Hết tất cả các lệnh cấm", "category": "HIỆU LỆNH", "action": "Đã hết hiệu lực của các biển cấm trước đó", "speed_limit": None},
    "P.101": {"name": "Đường cấm", "category": "CẤM", "action": "Đường cấm tất cả các loại phương tiện đi lại cả hai hướng", "speed_limit": None},
    "P.102": {"name": "Cấm đi ngược chiều", "category": "CẤM", "action": "Cấm tất cả các loại xe đi vào theo chiều đặt biển", "speed_limit": None},
    "P.103a": {"name": "Cấm xe ô tô", "category": "CẤM", "action": "Cấm tất cả các loại xe cơ giới từ 3 bánh trở lên đi vào", "speed_limit": None},
    "P.103b": {"name": "Cấm ô tô rẽ phải", "category": "CẤM", "action": "Cấm các loại xe cơ giới từ 3 bánh trở lên rẽ phải", "speed_limit": None},
    "P.103c": {"name": "Cấm ô tô rẽ trái", "category": "CẤM", "action": "Cấm các loại xe cơ giới từ 3 bánh trở lên rẽ trái", "speed_limit": None},
    "P.104": {"name": "Cấm xe máy", "category": "CẤM", "action": "Cấm các loại xe mô tô hai bánh và ba bánh", "speed_limit": None},
    "P.105": {"name": "Cấm ô tô và xe máy", "category": "CẤM", "action": "Cấm các loại xe cơ giới và xe mô tô", "speed_limit": None},
    "P.106a": {"name": "Cấm xe ô tô tải", "category": "CẤM", "action": "Cấm các loại xe ô tô tải trừ xe ưu tiên", "speed_limit": None},
    "P.106b": {"name": "Cấm xe tải trên 3.5 tấn", "category": "CẤM", "action": "Cấm ô tô tải có khối lượng chuyên chở lớn hơn 3.5 tấn", "speed_limit": None},
    "P.107a": {"name": "Cấm xe ô tô khách", "category": "CẤM", "action": "Cấm ô tô chở khách từ 9 chỗ trở lên", "speed_limit": None},
    "P.107b": {"name": "Cấm xe ô tô tải và ô tô khách", "category": "CẤM", "action": "Cấm cả ô tô tải và ô tô khách", "speed_limit": None},
    "P.108": {"name": "Cấm ô tô kéo rơ-moóc", "category": "CẤM", "action": "Cấm các loại xe cơ giới kéo theo rơ-moóc", "speed_limit": None},
    "P.112": {"name": "Cấm người đi bộ", "category": "CẤM", "action": "Cấm người đi bộ qua lại trên đoạn đường này", "speed_limit": None},
    "P.115": {"name": "Hạn chế trọng tải toàn bộ xe", "category": "CẤM", "action": "Cấm xe có trọng lượng vượt quá trị số ghi trên biển", "speed_limit": None},
    "P.116": {"name": "Hạn chế tải trọng trên trục xe", "category": "CẤM", "action": "Cấm xe có tải trọng trục vượt quá mức quy định", "speed_limit": None},
    "P.117": {"name": "Hạn chế chiều cao xe", "category": "CẤM", "action": "Cấm các xe có chiều cao vượt quá chỉ số ghi trên biển", "speed_limit": None},
    "P.118": {"name": "Hạn chế chiều ngang xe", "category": "CẤM", "action": "Cấm các xe có chiều ngang vượt quá mức ghi trên biển", "speed_limit": None},
    "P.119": {"name": "Hạn chế chiều dài xe", "category": "CẤM", "action": "Cấm các xe có chiều dài vượt quá mức quy định", "speed_limit": None},
    "P.120": {"name": "Hạn chế chiều dài xe kéo rơ-moóc", "category": "CẤM", "action": "Cấm xe kéo theo rơ-moóc có tổng chiều dài vượt quá", "speed_limit": None},
    "P.121": {"name": "Cự ly tối thiểu giữa hai xe", "category": "CẤM", "action": "Xe ô tô phải đi cách nhau một khoảng cách tối thiểu ghi trên biển", "speed_limit": None},
    "P.123a": {"name": "Cấm rẽ trái", "category": "CẤM", "action": "Cấm các loại phương tiện cơ giới và thô sơ rẽ trái", "speed_limit": None},
    "P.123b": {"name": "Cấm rẽ phải", "category": "CẤM", "action": "Cấm các loại phương tiện cơ giới và thô sơ rẽ phải", "speed_limit": None},
    "P.124a": {"name": "Cấm quay đầu xe", "category": "CẤM", "action": "Cấm các loại phương tiện quay đầu xe theo kiểu chữ U", "speed_limit": None},
    "P.124b": {"name": "Cấm ô tô quay đầu xe", "category": "CẤM", "action": "Cấm xe ô tô quay đầu xe theo kiểu chữ U", "speed_limit": None},
    "P.124c": {"name": "Cấm rẽ trái và quay đầu xe", "category": "CẤM", "action": "Cấm các phương tiện rẽ trái đồng thời cấm quay đầu xe", "speed_limit": None},
    "P.124d": {"name": "Cấm rẽ phải và quay đầu xe", "category": "CẤM", "action": "Cấm các phương tiện rẽ phải đồng thời cấm quay đầu xe", "speed_limit": None},
    "P.125": {"name": "Cấm vượt", "category": "CẤM", "action": "Cấm các loại xe cơ giới vượt nhau trên đoạn đường này", "speed_limit": None},
    "P.126": {"name": "Cấm ô tô tải vượt", "category": "CẤM", "action": "Cấm các loại ô tô tải vượt các xe cơ giới khác", "speed_limit": None},
    "P.127": {"name": "Tốc độ tối đa cho phép", "category": "CẤM", "action": "Chạy dưới hoặc bằng tốc độ tối đa ghi trên mặt biển", "speed_limit": 50},
    "P.128": {"name": "Cấm sử dụng còi", "category": "CẤM", "action": "Không được bấm còi xe trong khu vực đặt biển", "speed_limit": None},
    "P.130": {"name": "Cấm dừng xe và đỗ xe", "category": "CẤM", "action": "Cấm tất cả phương tiện dừng xe và đỗ xe ở đoạn đường này", "speed_limit": None},
    "P.131a": {"name": "Cấm đỗ xe", "category": "CẤM", "action": "Cấm tất cả các phương tiện đỗ xe ở đoạn đường đặt biển", "speed_limit": None},
    "P.131b": {"name": "Cấm đỗ xe ngày lẻ", "category": "CẤM", "action": "Cấm đỗ xe vào các ngày lẻ trong tháng", "speed_limit": None},
    "P.131c": {"name": "Cấm đỗ xe ngày chẵn", "category": "CẤM", "action": "Cấm đỗ xe vào các ngày chẵn trong tháng", "speed_limit": None},
    "P.132": {"name": "Nhường đường cho xe ngược chiều", "category": "CẤM", "action": "Phải nhường đường cho xe cơ giới đi ngược chiều qua đường hẹp", "speed_limit": None},
    "P.137": {"name": "Cấm rẽ trái và rẽ phải", "category": "CẤM", "action": "Cấm các phương tiện rẽ trái và rẽ phải tại ngã ba/ngã tư", "speed_limit": None},
    "P.245a": {"name": "Đi chậm", "category": "CẤM", "action": "Giảm tốc độ và chú ý quan sát cẩn thận", "speed_limit": None},

    # 2. BIỂN HIỆU LỆNH (Nhóm R)
    "R.301a": {"name": "Các xe chỉ được đi thẳng", "category": "HIỆU LỆNH", "action": "Các phương tiện chỉ được phép đi thẳng", "speed_limit": None},
    "R.301b": {"name": "Các xe chỉ được rẽ phải", "category": "HIỆU LỆNH", "action": "Các phương tiện chỉ được phép rẽ sang phải", "speed_limit": None},
    "R.301c": {"name": "Các xe chỉ được rẽ trái", "category": "HIỆU LỆNH", "action": "Các phương tiện chỉ được phép rẽ sang trái", "speed_limit": None},
    "R.301d": {"name": "Các xe chỉ được rẽ phải", "category": "HIỆU LỆNH", "action": "Chỉ được phép rẽ phải ở phạm vi ngã ba, ngã tư", "speed_limit": None},
    "R.301e": {"name": "Các xe chỉ được đi thẳng và rẽ trái", "category": "HIỆU LỆNH", "action": "Chỉ được phép đi thẳng hoặc rẽ trái", "speed_limit": None},
    "R.301f": {"name": "Các xe chỉ được đi thẳng và rẽ phải", "category": "HIỆU LỆNH", "action": "Chỉ được phép đi thẳng hoặc rẽ phải", "speed_limit": None},
    "R.302a": {"name": "Hướng phải đi vòng sang phải", "category": "HIỆU LỆNH", "action": "Phải đi vòng tránh chướng ngại vật sang bên phải", "speed_limit": None},
    "R.302b": {"name": "Hướng phải đi vòng sang trái", "category": "HIỆU LỆNH", "action": "Phải đi vòng tránh chướng ngại vật sang bên trái", "speed_limit": None},
    "R.303": {"name": "Nơi giao nhau chạy theo vòng xuyến", "category": "HIỆU LỆNH", "action": "Chạy vòng quanh đảo an toàn theo chiều mũi tên", "speed_limit": None},
    "R.304": {"name": "Đường dành cho xe thô sơ", "category": "HIỆU LỆNH", "action": "Đoạn đường chỉ dành riêng cho xe thô sơ và người đi bộ", "speed_limit": None},
    "R.305": {"name": "Đường dành cho người đi bộ", "category": "HIỆU LỆNH", "action": "Đoạn đường chỉ dành riêng cho người đi bộ", "speed_limit": None},
    "R.306": {"name": "Tốc độ tối thiểu cho phép", "category": "HIỆU LỆNH", "action": "Chạy với tốc độ lớn hơn hoặc bằng tốc độ ghi trên biển", "speed_limit": None},
    "R.403a": {"name": "Đường dành cho xe ô tô", "category": "HIỆU LỆNH", "action": "Bắt đầu đoạn đường dành riêng cho xe ô tô lưu thông", "speed_limit": None},
    "R.407a": {"name": "Đường một chiều", "category": "CHỈ DẪN", "action": "Đoạn đường chỉ lưu thông theo một chiều quy định", "speed_limit": None},
    "R.409": {"name": "Chỗ quay xe", "category": "CHỈ DẪN", "action": "Vị trí được phép quay đầu xe an toàn", "speed_limit": None},
    "R.425": {"name": "Bệnh viện", "category": "CHỈ DẪN", "action": "Gần bệnh viện, cơ sở cấp cứu, hạn chế bấm còi", "speed_limit": None},
    "R.434": {"name": "Bến xe buýt", "category": "CHỈ DẪN", "action": "Điểm dừng đón trả khách của xe buýt", "speed_limit": None},

    # 3. BIỂN CẢNH BÁO NGUY HIỂM (Nhóm W)
    "W.201a": {"name": "Chỗ ngoặt nguy hiểm vòng bên trái", "category": "CẢNH BÁO", "action": "Đoạn đường cong gấp nguy hiểm về phía bên trái", "speed_limit": None},
    "W.201b": {"name": "Chỗ ngoặt nguy hiểm vòng bên phải", "category": "CẢNH BÁO", "action": "Đoạn đường cong gấp nguy hiểm về phía bên phải", "speed_limit": None},
    "W.202a": {"name": "Nhiều chỗ ngoặt nguy hiểm liên tiếp vòng bên trái", "category": "CẢNH BÁO", "action": "Đoạn đường nhiều khúc cua liên tiếp đầu tiên sang trái", "speed_limit": None},
    "W.202b": {"name": "Nhiều chỗ ngoặt nguy hiểm liên tiếp vòng bên phải", "category": "CẢNH BÁO", "action": "Đoạn đường nhiều khúc cua liên tiếp đầu tiên sang phải", "speed_limit": None},
    "W.203a": {"name": "Đường bị hẹp cả hai bên", "category": "CẢNH BÁO", "action": "Mặt đường bị hẹp đột ngột từ cả hai phía", "speed_limit": None},
    "W.203b": {"name": "Đường bị hẹp về phía trái", "category": "CẢNH BÁO", "action": "Mặt đường bị hẹp đột ngột về phía bên trái", "speed_limit": None},
    "W.203c": {"name": "Đường bị hẹp về phía phải", "category": "CẢNH BÁO", "action": "Mặt đường bị hẹp đột ngột về phía bên phải", "speed_limit": None},
    "W.205a": {"name": "Đường giao nhau cùng mức (ngã tư)", "category": "CẢNH BÁO", "action": "Giao nhau cùng mức của các tuyến đường cùng cấp", "speed_limit": None},
    "W.205b": {"name": "Đường giao nhau nhánh bên phải", "category": "CẢNH BÁO", "action": "Giao nhau cùng mức với đường cùng cấp phía bên phải", "speed_limit": None},
    "W.205c": {"name": "Đường giao nhau nhánh bên trái", "category": "CẢNH BÁO", "action": "Giao nhau cùng mức với đường cùng cấp phía bên trái", "speed_limit": None},
    "W.205d": {"name": "Đường giao nhau ngã ba chữ T", "category": "CẢNH BÁO", "action": "Đoạn đường giao nhau dạng chữ T, chuẩn bị giảm tốc", "speed_limit": None},
    "W.205e": {"name": "Đường giao nhau ngã ba chữ Y", "category": "CẢNH BÁO", "action": "Đoạn đường tách nhánh dạng chữ Y", "speed_limit": None},
    "W.207a": {"name": "Giao nhau với đường không ưu tiên", "category": "CẢNH BÁO", "action": "Đang đi trên đường ưu tiên qua ngã ba/ngã tư", "speed_limit": None},
    "W.207b": {"name": "Giao nhau với đường không ưu tiên bên phải", "category": "CẢNH BÁO", "action": "Có đường nhánh không ưu tiên nhập vào bên phải", "speed_limit": None},
    "W.207c": {"name": "Giao nhau với đường không ưu tiên bên trái", "category": "CẢNH BÁO", "action": "Có đường nhánh không ưu tiên nhập vào bên trái", "speed_limit": None},
    "W.208": {"name": "Giao nhau với đường ưu tiên", "category": "CẢNH BÁO", "action": "Phải nhường đường cho các xe đi trên đường ưu tiên", "speed_limit": None},
    "W.209": {"name": "Nơi giao nhau có tín hiệu đèn", "category": "CẢNH BÁO", "action": "Sắp đến nơi giao nhau có đèn tín hiệu giao thông", "speed_limit": None},
    "W.210": {"name": "Giao nhau với đường sắt có rào chắn", "category": "CẢNH BÁO", "action": "Đoạn đường sắt giao nhau có rào chắn bảo vệ", "speed_limit": None},
    "W.211a": {"name": "Giao nhau với đường sắt không có rào chắn", "category": "CẢNH BÁO", "action": "Đường sắt cắt ngang không rào chắn, chú ý dừng lại quan sát", "speed_limit": None},
    "W.219": {"name": "Dốc xuống nguy hiểm", "category": "CẢNH BÁO", "action": "Đoạn dốc xuống dài và nguy hiểm, đi số thấp", "speed_limit": None},
    "W.221b": {"name": "Đường có gờ giảm tốc", "category": "CẢNH BÁO", "action": "Mặt đường có gờ lồi lõm giảm tốc, đi chậm lại", "speed_limit": None},
    "W.224": {"name": "Đường người đi bộ cắt ngang", "category": "CẢNH BÁO", "action": "Giảm tốc độ, chú ý nhường đường cho người đi bộ", "speed_limit": None},
    "W.225": {"name": "Trẻ em qua đường", "category": "CẢNH BÁO", "action": "Khu vực trường học hoặc sân chơi trẻ em, đi chậm", "speed_limit": None},
    "W.227": {"name": "Công trường đang thi công", "category": "CẢNH BÁO", "action": "Đoạn đường đang sửa chữa hoặc thi công, giảm tốc độ", "speed_limit": None},
    "W.233": {"name": "Nguy hiểm khác", "category": "CẢNH BÁO", "action": "Khu vực tiềm ẩn nguy hiểm bất ngờ không có biển báo riêng", "speed_limit": None},
    "W.235": {"name": "Đường đôi", "category": "CẢNH BÁO", "action": "Bắt đầu đoạn đường đôi có dải phân cách giữa", "speed_limit": None},
    "W.245a": {"name": "Đi chậm", "category": "CẢNH BÁO", "action": "Đoạn đường nguy hiểm, các phương tiện cần đi chậm", "speed_limit": None},

    # 4. BIỂN PHỤ & CHỈ DẪN (Nhóm S & I)
    "S.508": {"name": "Thời gian hiệu lực", "category": "BIỂN PHỤ", "action": "Hiệu lực biển báo áp dụng theo khung giờ chỉ định", "speed_limit": None},
    "S.503": {"name": "Phạm vi đối tượng áp dụng", "category": "BIỂN PHỤ", "action": "Chỉ định loại xe hoặc đối tượng cụ thể áp dụng", "speed_limit": None},
    "S.509a": {"name": "Thuyết minh biển báo", "category": "BIỂN PHỤ", "action": "Bổ sung thông tin giải thích cho biển chính", "speed_limit": None},
    "I.401": {"name": "Bắt đầu đường ưu tiên", "category": "CHỈ DẪN", "action": "Đoạn đường được quyền ưu tiên qua nơi giao nhau", "speed_limit": None},
    "I.402": {"name": "Hết đoạn đường ưu tiên", "category": "CHỈ DẪN", "action": "Kết thúc quyền ưu tiên qua nơi giao nhau", "speed_limit": None},
    "I.408a": {"name": "Nơi đỗ xe", "category": "CHỈ DẪN", "action": "Khu vực được phép đỗ xe", "speed_limit": None},
    "I.423a": {"name": "Vị trí người đi bộ sang đường", "category": "CHỈ DẪN", "action": "Vị trí quy định cho người đi bộ qua đường", "speed_limit": None},
}

_onnx_sess = None
_ocr_reader = None
_qcvn_classifier_sess = None
_qcvn_classes_list = None
QCVN_CLASSIFIER_PATH = BASE_DIR / "backend" / "app" / "assets" / "qcvn_sign_classifier.onnx"
QCVN_CLASSES_PATH = BASE_DIR / "backend" / "app" / "assets" / "qcvn_classes.json"

def get_sign_onnx_session():
    global _onnx_sess
    if _onnx_sess is None and MODEL_PATH.exists():
        try:
            import onnxruntime as ort
            _onnx_sess = ort.InferenceSession(str(MODEL_PATH), providers=['CPUExecutionProvider'])
        except Exception as e:
            print("Cannot load sign ONNX on backend:", e)
    return _onnx_sess


def get_ocr_reader():
    global _ocr_reader
    if _ocr_reader is None:
        try:
            import easyocr
            _ocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        except Exception as e:
            print("EasyOCR init exception:", e)
    return _ocr_reader


def get_qcvn_classifier():
    global _qcvn_classifier_sess, _qcvn_classes_list
    if _qcvn_classifier_sess is None and QCVN_CLASSIFIER_PATH.exists():
        try:
            import json
            import onnxruntime as ort
            _qcvn_classifier_sess = ort.InferenceSession(str(QCVN_CLASSIFIER_PATH), providers=['CPUExecutionProvider'])
            if QCVN_CLASSES_PATH.exists():
                with open(str(QCVN_CLASSES_PATH), 'r', encoding='utf-8') as f:
                    _qcvn_classes_list = json.load(f)
        except Exception as e:
            print("Cannot load QCVN classifier ONNX:", e)
    return _qcvn_classifier_sess, _qcvn_classes_list


def classify_crop_with_qcvn(crop: np.ndarray) -> Optional[Tuple[str, float]]:
    """Phân loại hình cắt biển báo bằng mô hình CNN QCVN 154 lớp đã huấn luyện"""
    if crop is None or crop.shape[0] < 16 or crop.shape[1] < 16:
        return None
    sess, classes = get_qcvn_classifier()
    if sess is None or not classes:
        return None
    try:
        crop_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        crop_res = cv2.resize(crop_rgb, (64, 64)).astype(np.float32) / 255.0
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        norm = (crop_res - mean) / std
        inp = np.expand_dims(norm.transpose(2, 0, 1), axis=0)
        out = sess.run(None, {sess.get_inputs()[0].name: inp})[0][0]
        exp = np.exp(out - np.max(out))
        probs = exp / np.sum(exp)
        top_idx = int(np.argmax(probs))
        top_prob = float(probs[top_idx])
        meta = classes[top_idx]
        return meta.get('code', 'P.100'), top_prob
    except Exception as e:
        print("classify_crop_with_qcvn error:", e)
        return None


def extract_aux_time_from_crop(crop: np.ndarray) -> Optional[str]:
    """
    Trích xuất khung giờ hiệu lực từ biển phụ S.508 với độ chính xác cao.
    Áp dụng phóng đại 3x INTER_CUBIC, CLAHE cân bằng tương phản và OCR chuẩn hóa ký tự.
    """
    if crop is None or crop.shape[0] < 8 or crop.shape[1] < 12:
        return None
    reader = get_ocr_reader()
    if reader is None:
        return None
    try:
        h, w = crop.shape[:2]
        up = cv2.resize(crop, (w * 3, h * 3), interpolation=cv2.INTER_CUBIC)
        gray = cv2.cvtColor(up, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(4, 4))
        enhanced = clahe.apply(gray)
        
        txts = reader.readtext(enhanced, detail=0)
        raw = " ".join(txts)
        clean = raw.replace(",", ":").replace(".", ":").replace("h", ":").replace("H", ":")
        clean = re.sub(r"\s+", "", clean)
        m = re.search(r"(\d{1,2}:\d{2})[-–~](\d{1,2}:\d{2})", clean)
        if m:
            return f"{m.group(1)} - {m.group(2)}"
        m2 = re.search(r"(\d{1,2})[:h]?(\d{2})?[-–~](\d{1,2})[:h]?(\d{2})?", clean)
        if m2:
            sh = m2.group(1)
            sm = m2.group(2) or "00"
            eh = m2.group(3)
            em = m2.group(4) or "00"
            return f"{sh}:{sm} - {eh}:{em}"
    except Exception as e:
        print("extract_aux_time_from_crop error:", e)
    return None


class TrafficSignItem(BaseModel):
    sign_type: str
    name: str
    category: str
    speed_limit: Optional[int] = None
    confidence: float
    bbox: List[int]
    action_required: str
    thumbnail: Optional[str] = None
    time_window: Optional[str] = None


class TrafficSignResponse(BaseModel):
    success: bool
    processing_time_ms: float
    image_width: int
    image_height: int
    signs: List[TrafficSignItem]
    traffic_signs: Optional[List[TrafficSignItem]] = None


def _detect_signs_with_onnx(img: np.ndarray, conf_thresh: float = 0.20):
    sess = get_sign_onnx_session()
    if sess is None:
        return []
    
    H, W = img.shape[:2]
    S = 640
    sc = min(S / W, S / H)
    nw, nh = int(W * sc), int(H * sc)
    px, py = (S - nw) // 2, (S - nh) // 2
    
    resized = cv2.resize(img, (nw, nh))
    canvas = np.full((S, S, 3), 114, dtype=np.uint8)
    canvas[py:py+nh, px:px+nw] = resized
    
    inp = canvas.transpose(2, 0, 1).astype(np.float32) / 255.0
    inp = np.expand_dims(inp, axis=0)
    
    out = sess.run(None, {sess.get_inputs()[0].name: inp})[0]
    classes_scores = out[0, 4:, :]
    max_scores = np.max(classes_scores, axis=0)
    best_cls = np.argmax(classes_scores, axis=0)
    
    indices = np.where(max_scores >= conf_thresh)[0]
    detections = []
    
    for idx in indices:
        s = float(max_scores[idx])
        c = int(best_cls[idx])
        cx = float(out[0, 0, idx])
        cy = float(out[0, 1, idx])
        w = float(out[0, 2, idx])
        h = float(out[0, 3, idx])
        
        x1 = max(0, int((cx - w / 2 - px) / sc))
        y1 = max(0, int((cy - h / 2 - py) / sc))
        x2 = min(W, int((cx + w / 2 - px) / sc))
        y2 = min(H, int((cy + h / 2 - py) / sc))
        
        sign_code = SIGN_CLASSES_58[c] if c < len(SIGN_CLASSES_58) else "P.100"
        
        # Kiểm tra kích thước hình học tối thiểu
        bw_c = x2 - x1
        bh_c = y2 - y1
        if bw_c < 16 or bh_c < 16:
            continue
        asp_c = bw_c / max(1, bh_c)
        if asp_c < 0.50 or asp_c > 2.0:
            continue

        # Thẩm định màu sắc theo Quy chuẩn Báo hiệu Đường bộ QCVN 41:2019/BGTVT (chỉ loại trừ khi không phải ban đêm/ánh đèn vàng):
        crop = img[y1:y2, x1:x2]
        if crop.size > 0:
            chsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
            c_tot = max(1, crop.shape[0] * crop.shape[1])
            r1 = cv2.inRange(chsv, np.array([0, 50, 40]), np.array([14, 255, 255]))
            r2 = cv2.inRange(chsv, np.array([155, 50, 40]), np.array([180, 255, 255]))
            red_r = (np.count_nonzero(r1) + np.count_nonzero(r2)) / c_tot
            bl = cv2.inRange(chsv, np.array([90, 50, 40]), np.array([135, 255, 255]))
            blue_r = np.count_nonzero(bl) / c_tot
            yel = cv2.inRange(chsv, np.array([12, 50, 50]), np.array([36, 255, 255]))
            yel_r = np.count_nonzero(yel) / c_tot

            # 1. Biển Hiệu lệnh (R) và Chỉ dẫn (I) BẮT BUỘC là màu xanh lam (Blue):
            if (sign_code.startswith("R.") or sign_code.startswith("I.")) and not sign_code.startswith("R.4"):
                if blue_r < 0.05 and red_r >= 0.20 and s < 0.60:
                    continue  # Biển màu đỏ thuần tuyệt đối không thể là biển hiệu lệnh!

            # 2. Biển Cảnh báo (W) BẮT BUỘC là hình tam giác nền vàng viền đỏ:
            if sign_code.startswith("W."):
                if yel_r < 0.04 and red_r < 0.04 and s < 0.55:
                    continue

            # 3. Biển Cấm (P):
            if sign_code.startswith("P."):
                if not (sign_code.startswith("P.130") or sign_code.startswith("P.131")):
                    if red_r < 0.04 and s < 0.55:
                        continue
                    if blue_r >= 0.35:
                        continue
                    ref_c, _ = refine_prohibition_sign(crop)
                    if ref_c == "P.100" and s < 0.55:
                        continue  # Bỏ qua biển quảng cáo đỏ VinMart+ / biển hiệu cửa hàng


        detections.append({
            "sign_type": sign_code,
            "conf": s,
            "bbox": [x1, y1, x2, y2],
        })
        
    return _apply_nms(detections, iou_thresh=0.45)


def _apply_nms(dets: List[dict], iou_thresh: float = 0.40) -> List[dict]:
    if not dets:
        return []
    dets = sorted(dets, key=lambda d: d.get("conf", 0.5), reverse=True)
    kept = []
    for d in dets:
        overlap = False
        bx1, by1, bx2, by2 = d["bbox"]
        area_d = max(1, (bx2 - bx1) * (by2 - by1))
        cdx = (bx1 + bx2) / 2
        cdy = (by1 + by2) / 2
        d_type = d.get("sign_type", "")
        
        for k in kept:
            kx1, ky1, kx2, ky2 = k["bbox"]
            area_k = max(1, (kx2 - kx1) * (ky2 - ky1))
            ckx = (kx1 + kx2) / 2
            cky = (ky1 + ky2) / 2
            k_type = k.get("sign_type", "")
            
            xx1 = max(bx1, kx1)
            yy1 = max(by1, ky1)
            xx2 = min(bx2, kx2)
            yy2 = min(by2, ky2)
            inter = max(0, xx2 - xx1) * max(0, yy2 - yy1)
            union = area_d + area_k - inter
            iou = (inter / union) if union > 0 else 0
            
            center_dist = ((cdx - ckx) ** 2 + (cdy - cky) ** 2) ** 0.5
            min_area = min(area_d, area_k)
            
            # 1. Trùng lặp cùng loại biển báo nếu IoU > 0.35 hoặc bị lồng trọn nhau (>70% diện tích)
            if d_type == k_type and (iou > 0.35 or (inter / min_area) > 0.70):
                overlap = True
                break
                
            # 2. Cùng họ biển cấm ô tô P.103 (P.103a, P.103b, P.103c) nếu IoU > 0.35
            if d_type.startswith("P.103") and k_type.startswith("P.103") and (iou > 0.35 or (inter / min_area) > 0.70):
                overlap = True
                break

            # 3. Kiểm tra xem có bị bao trọn bên trong nhau (con số nằm trong biển)
            if inter / area_d > 0.65 or inter / area_k > 0.65:
                overlap = True
                break

            # 4. Kiểm tra IoU tiêu chuẩn
            if iou > iou_thresh:
                overlap = True
                break

            # 5. Hai box có tâm quá gần nhau (< 25px) trên cùng vị trí (trừ cặp biển chính P và biển phụ S)
            is_main_sub_pair = (d_type.startswith("S.") and not k_type.startswith("S.")) or (k_type.startswith("S."))
            if center_dist < 25 and not is_main_sub_pair:
                overlap = True
                break
        if not overlap:
            kept.append(d)
    return kept


def refine_p103_sign_class(crop: np.ndarray, initial_code: str = "P.103a", has_aux_sign: bool = False) -> str:
    """
    Phân loại chính xác giữa P.103a (Cấm xe ô tô), P.103b (Cấm ô tô rẽ phải), P.103c (Cấm ô tô rẽ trái)
    theo quy chuẩn QCVN 41:2019/BGTVT.
    """
    if has_aux_sign:
        # Trong tổ chức giao thông Việt Nam, biển cấm có gắn biển phụ xe hợp đồng / taxi / giờ cao điểm
        # 100% là biển P.103a (Cấm xe ô tô đi vào)
        return "P.103a"

    if crop is None or crop.shape[0] < 20 or crop.shape[1] < 20:
        return initial_code

    H, W = crop.shape[:2]
    ch1, ch2 = int(H * 0.20), int(H * 0.80)
    cw1, cw2 = int(W * 0.20), int(W * 0.80)
    center = crop[ch1:ch2, cw1:cw2]
    if center.size == 0:
        return initial_code

    gray_c = cv2.cvtColor(center, cv2.COLOR_BGR2GRAY)
    hsv_c = cv2.cvtColor(center, cv2.COLOR_BGR2HSV)
    red1 = cv2.inRange(hsv_c, np.array([0, 60, 45]), np.array([12, 255, 255]))
    red2 = cv2.inRange(hsv_c, np.array([160, 60, 45]), np.array([180, 255, 255]))
    red_slash = cv2.bitwise_or(red1, red2)

    black = (gray_c < 110) & (red_slash == 0)
    mid_w = center.shape[1] // 2
    lb = np.count_nonzero(black[:, :mid_w])
    rb = np.count_nonzero(black[:, mid_w:])

    if lb > 1.45 * rb:
        return "P.103c"
    elif rb > 1.45 * lb:
        return "P.103b"
    else:
        return "P.103a"


def refine_prohibition_sign(crop: np.ndarray, has_aux: bool = False) -> Tuple[str, float]:
    """
    Phân loại chính xác các biển cấm tròn viền đỏ theo QCVN 41:2019/BGTVT:
    - P.124b: Cấm ô tô quay đầu xe
    - P.124a: Cấm quay đầu xe
    - P.124c: Cấm rẽ trái và quay đầu xe
    - P.124d: Cấm rẽ phải và quay đầu xe
    - P.123a: Cấm rẽ trái
    - P.123b: Cấm rẽ phải
    - P.103a: Cấm xe ô tô (hoặc P.103b, P.103c)
    - P.102: Cấm đi ngược chiều
    - P.130 / P.131a: Cấm dừng/đỗ xe
    - P.101: Đường cấm
    LOẠI BỎ TRIỆT ĐỂ BIỂN QUẢNG CÁO ĐỎ / BIỂN HIỆU VINMART+ / BẢNG HIỆU NHÀ PHỐ
    """
    if crop is None or crop.shape[0] < 16 or crop.shape[1] < 16:
        return "P.100", 0.0

    H, W = crop.shape[:2]
    aspect = W / max(1, H)
    # 0. Biển cấm P bắt buộc là hình tròn: 0.65 <= aspect <= 1.45
    if aspect < 0.65 or aspect > 1.45:
        return "P.100", 0.0

    # Chuẩn hóa về độ phân giải chuẩn 80x80 để đảm bảo đếm pixel chính xác bất kể khoảng cách
    if H != 80 or W != 80:
        work_crop = cv2.resize(crop, (80, 80), interpolation=cv2.INTER_CUBIC)
    else:
        work_crop = crop
    H, W = 80, 80

    gray = cv2.cvtColor(work_crop, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(work_crop, cv2.COLOR_BGR2HSV)
    
    # 1. Đo màu sắc
    r1 = cv2.inRange(hsv, np.array([0, 50, 40]), np.array([14, 255, 255]))
    r2 = cv2.inRange(hsv, np.array([155, 50, 40]), np.array([180, 255, 255]))
    red = cv2.bitwise_or(r1, r2)
    
    blue = cv2.inRange(hsv, np.array([95, 60, 45]), np.array([130, 255, 255]))
    blue_ratio = np.count_nonzero(blue) / max(1, H * W)
    red_ratio = np.count_nonzero(red) / max(1, H * W)

    # 2. Vùng ruột bên trong vòng tròn đỏ (bán kính 0.38)
    ch, cw = H // 2, W // 2
    Y, X = np.ogrid[:H, :W]
    dist = np.sqrt((X - cw)**2 + (Y - ch)**2)
    inner_mask = dist <= (min(H, W) * 0.38)
    inner_area = max(1, np.count_nonzero(inner_mask))
    
    inner_red_ratio = np.count_nonzero(red & inner_mask) / inner_area
    inner_blue_ratio = np.count_nonzero(blue & inner_mask) / inner_area
    inner_white_ratio = np.count_nonzero((gray > 120) & inner_mask) / inner_area

    # A. Biển cấm dừng / đỗ (P.130 chữ X, P.131a vạch chéo trên nền xanh tròn)
    # BẮT BUỘC PHẢI CÓ CẢ MÀU XANH DƯƠNG VÀ VIỀN ĐỎ / VẠCH ĐỎ!
    if (blue_ratio > 0.15 or inner_blue_ratio > 0.15) and (red_ratio >= 0.07 or inner_red_ratio >= 0.05):
        return ("P.130", 0.95) if red_ratio > 0.28 else ("P.131a", 0.94)

    black_pix = (gray < 112) & (red == 0) & inner_mask
    n_black = np.count_nonzero(black_pix)

    # B. LOẠI TRỪ BIỂN QUẢNG CÁO ĐỎ / BIỂN HIỆU VINMART+ / BIỂN P.102:
    # Biển P.102 (Cấm đi ngược chiều) ruột đỏ đặc, có vạch trắng ngang, TUYỆT ĐỐI KHÔNG CÓ KÝ HIỆU ĐEN
    center_box = dist <= (min(H, W) * 0.25)
    c_red_ratio = np.count_nonzero(red & center_box) / max(1, np.count_nonzero(center_box))
    if c_red_ratio > 0.52 and inner_red_ratio > 0.52 and n_black < 15:
        mid_strip = gray[int(H * 0.38): int(H * 0.62), int(W * 0.20): int(W * 0.80)]
        top_red_r = np.count_nonzero(red[int(H * 0.05):int(H * 0.25), int(W * 0.2): int(W * 0.8)]) / max(1, int(H * 0.20) * int(W * 0.60))
        bot_red_r = np.count_nonzero(red[int(H * 0.75):int(H * 0.95), int(W * 0.2): int(W * 0.8)]) / max(1, int(H * 0.20) * int(W * 0.60))
        if mid_strip.size > 0 and (np.count_nonzero(mid_strip > 155) / mid_strip.size) > 0.30:
            if top_red_r > 0.30 and bot_red_r > 0.30:
                return "P.102", 0.98
        return "P.100", 0.0

    # C. Với tất cả các biển cấm tròn thông thường (P.101, P.103..P.128...):
    # Nền ruột bên trong BẮT BUỘC là màu trắng / sáng:
    if inner_white_ratio < 0.18:
        return "P.100", 0.0  # Không có ruột trắng -> Bỏ qua, không phải biển cấm!

    # Viền đỏ ngoài bắt buộc phải có:
    if red_ratio < 0.06:
        return "P.100", 0.0

    # P.101 Đường cấm: ruột trắng tinh không có chi tiết đen
    if n_black < max(12, int(0.02 * inner_area)) and inner_white_ratio >= 0.38:
        return "P.101", 0.96

    # Phân tích hình học chi tiết các nhánh mũi tên và ký hiệu
    tl = np.count_nonzero(black_pix[:ch, :cw])
    tr = np.count_nonzero(black_pix[:ch, cw:])
    bl = np.count_nonzero(black_pix[ch:, :cw])
    br = np.count_nonzero(black_pix[ch:, cw:])

    top_far_l = np.count_nonzero(black_pix[:int(H * 0.48), :max(1, cw - int(W * 0.08))])
    top_far_r = np.count_nonzero(black_pix[:int(H * 0.48), cw + int(W * 0.08):])
    far_right = np.count_nonzero(black_pix[:, int(W * 0.65):])
    far_left = np.count_nonzero(black_pix[:, :int(W * 0.35)])

    # 1. Cấm rẽ phải P.123b:
    # Chân trụ ở nửa trái dưới (BL), uốn cong vươn sang nửa phải trên (TR). Góc dưới phải (BR) hầu như không có
    if bl > 15 and tr > 15 and br < max(12, int(bl * 0.18)):
        return "P.123b", 0.98

    # 2. Cấm rẽ trái P.123a:
    # Chân trụ ở nửa phải dưới (BR), uốn cong vươn sang nửa trái trên (TL). Góc dưới trái (BL) hầu như không có
    if br > 15 and tl > 15 and bl < max(12, int(br * 0.18)):
        return "P.123a", 0.98

    # 3. Nhóm U-turn và rẽ kết hợp (P.124a, P.124b, P.124c, P.124d):
    has_u_arch = (top_far_l > 15 and top_far_r > 15) or (bl > 20 and br > 20)
    if has_u_arch:
        if far_right > 30 and tr > 30:
            return "P.124d", 0.96  # Cấm rẽ phải và quay đầu
        if far_left > 30 and tl > 30:
            return "P.124c", 0.96  # Cấm rẽ trái và quay đầu
        if (tr > bl * 0.8 and br > bl * 0.4) or has_aux:
            return "P.124b", 0.95  # Cấm ô tô quay đầu
        return "P.124a", 0.98  # Cấm quay đầu xe

    # 4. Phân loại cấm ô tô (P.103a, P.103b, P.103c)
    p103_code = refine_p103_sign_class(crop, "P.103a", has_aux_sign=has_aux)
    return p103_code, 0.90


def clean_vietnamese_auxiliary_sign_text(raw_text: str) -> Tuple[str, str, str, Optional[str]]:
    """
    Chuẩn hóa văn bản nhận dạng từ biển phụ tiếng Việt theo QCVN 41:2019/BGTVT,
    khắc phục hoàn toàn lỗi sai font, lem luốc ký tự do OCR tiếng Anh.
    Trả về: (sign_code, name, action, time_str)
    """
    txt = raw_text.strip()
    txt = re.sub(r'[\[\]{}|<>~`@;!\"\'\\]', ' ', txt)
    txt = re.sub(r'\s+', ' ', txt).strip()

    # 1. Trích xuất khung giờ (VD: 6:00 - 22:00, 6.00-22.00, 6,00-22.00, 22.00-6.00, 6h - 22h, 16h30 - 19h30)
    # Chuẩn hóa dấu chấm/phẩy OCR nhầm từ dấu hai chấm ':'
    txt_norm = txt.replace(',', ':').replace('.', ':').replace('h', ':').replace('H', ':')
    txt_norm_clean = re.sub(r'\s*:\s*', ':', txt_norm)

    time_matches = re.findall(r'(\d{1,2}:\d{2})\s*[-–~]\s*(\d{1,2}:\d{2})', txt_norm_clean, flags=re.IGNORECASE)
    if not time_matches:
        # Match giờ không có phút hoặc phút viết tắt (VD: 6 - 22, 6:00 - 22:00, 22:00 - 6:00)
        m_h = re.findall(r'(\d{1,2})(?::(\d{2}))?\s*[-–~]\s*(\d{1,2})(?::(\d{2}))?', txt_norm_clean)
        if m_h:
            time_matches = [(f"{t1}:{t2 or '00'}", f"{t3}:{t4 or '00'}") for t1, t2, t3, t4 in m_h]

    formatted_times = []
    for t1, t2 in time_matches:
        formatted_times.append(f'{t1} - {t2}')
    time_str = ', '.join(formatted_times) if formatted_times else None

    upper = txt.upper()

    # 2. Nhận diện đối tượng (Xe hợp đồng, Taxi, Xe tải, Xe khách, ...)
    target_vehicle = None

    # Xe hợp đồng: HQP / HOP / H0P + DONG / D0NG / DonG
    is_hop_dong = bool(re.search(r'H[OQ0]P\s*D[O0N]NG', upper) or 'HOP DONG' in upper or 'HQP DONG' in upper)
    is_duoi = bool(re.search(r'(12\s*)?DUOI|DUDI|<', upper))
    is_tren = bool(re.search(r'TREN|TRÊN|>', upper))
    seat_match = re.search(r'(0?[1-9]|1[0-9]|2[0-9])\s*(CHO|CH0)\s*(NG[O0]I|NGOI)?', upper)
    seats = seat_match.group(1).lstrip('0') if seat_match else ('9' if is_hop_dong else None)

    if is_hop_dong:
        qualifier = f'dưới {seats} chỗ ngồi' if is_duoi or not is_tren else f'trên {seats} chỗ ngồi'
        target_vehicle = f'Xe hợp đồng {qualifier}'
    elif 'TAXI' in upper:
        target_vehicle = 'Xe taxi'
    elif re.search(r'XE\s*T[AÁ]I', upper) or 'TRUCK' in upper:
        ton_match = re.search(r'(\d+([\.,]\d+)?)\s*T[AẤ]N', upper)
        target_vehicle = f'Xe ô tô tải trên {ton_match.group(1)} tấn' if ton_match else 'Xe ô tô tải'
    elif re.search(r'XE\s*KH[AÁ]CH', upper) or 'BUS' in upper or re.search(r'XE\s*BU[YÝ]T', upper):
        target_vehicle = 'Xe ô tô khách'
    elif 'XE MAY' in upper or 'MOTO' in upper:
        target_vehicle = 'Xe mô tô, xe máy'

    # Xây dựng Name và Action chuẩn QCVN 41
    if target_vehicle and time_str:
        sign_code = 'S.508'
        name = f'{target_vehicle}'
        action = f'Hiệu lực áp dụng: {target_vehicle} ({time_str})'
    elif target_vehicle:
        sign_code = 'S.503'
        name = f'{target_vehicle}'
        action = f'Phạm vi đối tượng: Áp dụng đối với {target_vehicle}'
    elif time_str:
        sign_code = 'S.508'
        name = f'Khung giờ hiệu lực ({time_str})'
        action = f'Thời gian áp dụng hiệu lực: {time_str}'
    else:
        sign_code = 'S.509a'
        name = 'Thuyết minh bổ sung'
        action = f'Hiệu lực theo chỉ dẫn: {txt}'

    return sign_code, name, action, time_str


def _read_speed_limit_ocr(crop: np.ndarray) -> Optional[int]:
    """Đọc số tốc độ (20, 30, 40, 50, 60, 70, 80, 90, 100, 120) từ biển P.127"""
    if crop is None or crop.shape[0] < 25 or crop.shape[1] < 25:
        return None
    try:
        reader = get_ocr_reader()
        if reader is None:
            return None
        H, W = crop.shape[:2]
        center = crop[int(H * 0.15):int(H * 0.85), int(W * 0.15):int(W * 0.85)]
        gray = cv2.cvtColor(center, cv2.COLOR_BGR2GRAY)
        res = reader.readtext(gray)
        for _, text, conf in res:
            clean = ''.join(c for c in text if c.isdigit())
            if clean in ['20', '30', '40', '50', '60', '70', '80', '90', '100', '120']:
                return int(clean)
    except Exception:
        pass
    return None


def _classify_traffic_sign_crop(crop: np.ndarray) -> Optional[Tuple[str, Optional[int], float]]:
    """
    Phân loại chính xác biển báo Việt Nam kết hợp 118 mẫu chuẩn QCVN 41, thị giác máy tính và OCR
    """
    if crop is None or crop.shape[0] < 20 or crop.shape[1] < 20:
        return None
        
    H, W = crop.shape[:2]
    crop_aspect = W / max(1, H)
    if crop_aspect < 0.45 or crop_aspect > 2.35:
        return None

    # ── TẦNG 1: ĐỐI SOÁT SIÊU TỐC 118 BIỂN MẪU TỪ Bien_bao_giao_thong_Viet_Nam_md (~1ms) ──
    try:
        from backend.app.services.sign_template_matcher import SignTemplateMatcher
        matcher = SignTemplateMatcher.get_instance()
        matched = matcher.match_crop(crop)
        if matched is not None:
            tmpl, sim = matched
            if sim >= 0.74:
                speed_val = None
                if tmpl.code == "P.127":
                    speed_val = _read_speed_limit_ocr(crop) or 50
                return tmpl.code, speed_val, round(sim, 2)
    except Exception:
        pass

    # ── TẦNG 1.5: PHÂN LOẠI VỚI MÔ HÌNH CNN QCVN 154 LỚP (ĐÃ HUẤN LUYỆN CHUẨN XÁC) ──
    try:
        qcvn_pred = classify_crop_with_qcvn(crop)
        if qcvn_pred is not None:
            q_code, q_conf = qcvn_pred
            if q_conf >= 0.72:
                speed_val = _read_speed_limit_ocr(crop) if q_code == "P.127" else None
                return q_code, speed_val, round(q_conf, 2)
    except Exception:
        pass

    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    
    # 1. Đo các thành phần màu
    m_red1 = cv2.inRange(hsv, np.array([0, 55, 40]), np.array([12, 255, 255]))
    m_red2 = cv2.inRange(hsv, np.array([155, 55, 40]), np.array([180, 255, 255]))
    red_mask = cv2.bitwise_or(m_red1, m_red2)
    red_ratio = np.count_nonzero(red_mask) / (H * W)
    
    yellow_mask = cv2.inRange(hsv, np.array([15, 75, 75]), np.array([35, 255, 255]))
    yellow_ratio = np.count_nonzero(yellow_mask) / (H * W)
    
    blue_mask = cv2.inRange(hsv, np.array([95, 70, 45]), np.array([130, 255, 255]))
    blue_ratio = np.count_nonzero(blue_mask) / (H * W)
    
    # Lấy vùng trung tâm biển báo
    ch1, ch2 = int(H * 0.22), int(H * 0.78)
    cw1, cw2 = int(W * 0.22), int(W * 0.78)
    center = crop[ch1:ch2, cw1:cw2]
    c_area = max(1, center.shape[0] * center.shape[1])
    
    # Điểm ảnh màu đen bên trong
    black_mask = ((center[:, :, 0] < 80) & (center[:, :, 1] < 80) & (center[:, :, 2] < 80)).astype(np.uint8)
    black_ratio = np.count_nonzero(black_mask) / c_area
    
    # Điểm ảnh màu trắng / sáng bên trong
    gray_center = cv2.cvtColor(center, cv2.COLOR_BGR2GRAY)
    white_ratio = np.count_nonzero(gray_center > 135) / c_area
    
    # A. BIỂN CẤM (Viền đỏ)
    if red_ratio > 0.12 and 0.75 <= crop_aspect <= 1.30:
        # Nếu là đèn hậu hoặc đốm sáng ngoài đường (bên trong không có nền trắng/xanh) -> Bỏ qua
        if white_ratio < 0.20 and blue_ratio < 0.15:
            return None

        # 1. Biển cấm dừng / đỗ (P.130 chữ X, P.131a vạch chéo trên nền xanh tròn)
        if blue_ratio > 0.22 and red_ratio > 0.25:
            if red_ratio > 0.32:
                return "P.130", None, 0.94
            return "P.131a", None, 0.92

        # 2. Biển P.102 (Cấm đi ngược chiều): Nền đỏ tròn, vạch trắng ngang giữa
        if red_ratio > 0.38 and black_ratio < 0.04:
            mid_y = H // 2
            mid_strip = crop[max(0, mid_y - int(H * 0.12)): min(H, mid_y + int(H * 0.12)), int(W * 0.2): int(W * 0.8)]
            if mid_strip.size > 0:
                white_count = np.count_nonzero(np.all(mid_strip > 185, axis=2))
                strip_ratio = white_count / (mid_strip.shape[0] * mid_strip.shape[1])
                if strip_ratio > 0.45:
                    return "P.102", None, 0.97

        # 3. Biển tốc độ tối đa P.127: BẮT BUỘC phải đọc được con số tốc độ hợp lệ từ OCR
        speed = _read_speed_limit_ocr(crop)
        if speed is not None and speed in [20, 30, 40, 50, 60, 70, 80, 90, 100, 120]:
            return "P.127", speed, 0.98

        # 4. Phân loại các biển cấm khác (P.123, P.124, P.101, P.103...)
        ref_code, ref_conf = refine_prohibition_sign(crop)
        if ref_code != "P.100":
            return ref_code, None, ref_conf

    # B. BIỂN CẢNH BÁO NGUY HIỂM (Tam giác vàng viền đỏ)
    # BẮT BUỘC phải có viền đỏ bao quanh (red_ratio > 0.10) và nền vàng bên trong (yellow_ratio > 0.22)
    if yellow_ratio > 0.22 and red_ratio > 0.10:
        top_yellow = np.count_nonzero(yellow_mask[:int(H * 0.4), :])
        bot_yellow = np.count_nonzero(yellow_mask[int(H * 0.6):, :])
        # Tam giác ngược (W.208: Nhường đường)
        if top_yellow > bot_yellow * 1.8:
            return "W.208", None, 0.96

    # C. BIỂN HIỆU LỆNH (Tròn xanh chuẩn)
    # Không nhận diện bừa bãi chỉ dựa trên màu xanh nếu không khớp template
    return None


@router.post("/traffic-signs/detect", response_model=TrafficSignResponse)
@router.post("/traffic-sign/detect", response_model=TrafficSignResponse)
@router.post("/traffic-signs/detect-crop", response_model=TrafficSignResponse)
@router.post("/traffic-sign/detect-crop", response_model=TrafficSignResponse)
async def detect_traffic_signs_endpoint(file: UploadFile = File(...)):
    start_time = time.time()
    try:
        content = await file.read()
        nparr = np.frombuffer(content, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise HTTPException(status_code=400, detail="Không thể giải mã file ảnh tải lên")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Lỗi khi đọc file ảnh: {str(e)}")

    H, W = img.shape[:2]
    candidate_signs = []
    
    # ── GIAI ĐOẠN 1: CHẠY YOLO MODEL TRÊN TOÀN KHUNG HÌNH (Ngưỡng nhạy cảm conf >= 0.25) ──
    yolo_dets = _detect_signs_with_onnx(img, conf_thresh=0.25)
    for yd in yolo_dets:
        bx = yd["bbox"]
        x1, y1, x2, y2 = bx
        bw = x2 - x1
        bh = y2 - y1

        # LOẠI TRỪ 0: VẬT THỂ Ở QUÁ XA (Kích thước quá bé li ti < 22px, không đủ độ nét để đọc)
        if bw < 22 or bh < 22:
            continue

        # LOẠI TRỪ 0.1: TỶ LỆ HÌNH HỌC CHUẨN BIỂN BÁO (Tròn, vuông hoặc tam giác đều)
        aspect = bw / max(1, bh)
        if aspect < 0.65 or aspect > 1.50:
            continue

        # LOẠI TRỪ 1: VÙNG LÒNG ĐƯỜNG TRỰC DIỆN TRƯỚC MŨI XE
        # Chỉ áp dụng loại trừ lòng đường nếu bức ảnh là ảnh toàn cảnh dashcam (vật thể nhỏ so với khung hình)
        # Nếu là ảnh chụp cận cảnh biển báo hoặc ảnh crop (bw > 0.25*W hoặc W <= 600), KHÔNG loại trừ!
        is_close_up = (bw > W * 0.25) or (bh > H * 0.25) or (W <= 600)
        if not is_close_up:
            if x1 > (W * 0.32) and x2 < (W * 0.68) and y1 > (H * 0.32):
                continue  # ĐÂY LÀ ĐUÔI XE Ô TÔ / BIỂN SỐ XE, KHÔNG PHẢI BIỂN BÁO!

            # LOẠI TRỪ 2: Sát mặt đường
            if y2 > (H * 0.72):
                continue

            # LOẠI TRỪ 3: Góc ban công nhà cao tầng trên trời (cửa sổ / tường nhà)
            if y1 < (H * 0.08) and (x2 < (W * 0.22) or x1 > (W * 0.78)):
                continue

        crop = img[max(0, y1):min(H, y2), max(0, x1):min(W, x2)]
        if crop.size == 0:
            continue

        # LOẠI TRỪ 3.1: ĐỘ SẮC NÉT (SHARPNESS / LAPLACIAN VARIANCE)
        # Chỉ loại trừ khi độ nét quá thấp VÀ độ tin cậy của YOLO cũng thấp (< 0.65)
        # Đối với biển báo rõ màu ở hậu cảnh có bokeh/DOF, YOLO tin cậy cao (conf >= 0.65) vẫn được giữ lại
        gray_c = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        lap_var = cv2.Laplacian(gray_c, cv2.CV_64F).var()
        if lap_var < 26.0 and yd.get("conf", 0.0) < 0.65:
            continue

        # LOẠI TRỪ 4: KIỂM TRA MÀU SẮC ĐẶC TRƯNG CỦA BIỂN BÁO (Color Verification)
        hsv_c = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        m_r1 = cv2.inRange(hsv_c, np.array([0, 50, 40]), np.array([14, 255, 255]))
        m_r2 = cv2.inRange(hsv_c, np.array([155, 50, 40]), np.array([180, 255, 255]))
        m_red = cv2.bitwise_or(m_r1, m_r2)
        red_ratio = np.count_nonzero(m_red) / max(1, crop.shape[0] * crop.shape[1])

        m_blue = cv2.inRange(hsv_c, np.array([95, 60, 45]), np.array([130, 255, 255]))
        blue_ratio = np.count_nonzero(m_blue) / max(1, crop.shape[0] * crop.shape[1])

        m_yellow = cv2.inRange(hsv_c, np.array([12, 60, 60]), np.array([36, 255, 255]))
        yellow_ratio = np.count_nonzero(m_yellow) / max(1, crop.shape[0] * crop.shape[1])

        raw_code = yd["sign_type"]
        # Biển cấm P: Không áp dụng bộ lọc màu ban ngày cho P.130/P.131a
        if raw_code.startswith("P.") or raw_code.startswith("P"):
            is_parking_ban = raw_code.startswith("P.130") or raw_code.startswith("P.131")
            if not is_parking_ban:
                if red_ratio < 0.08 and yd["conf"] < 0.60:
                    continue
                center_c = gray_c[int(bh * 0.22):int(bh * 0.78), int(bw * 0.22):int(bw * 0.78)]
                c_white = np.count_nonzero(center_c > 125) / max(1, center_c.size)
                if c_white < 0.12 and blue_ratio < 0.15 and yd["conf"] < 0.60:
                    continue  # Đốm đỏ đặc không có ruột trắng -> Đèn hậu xe, bỏ qua!

        # Biển hiệu lệnh R bắt buộc phải có màu xanh dương (loại bỏ cây xanh!)
        if (raw_code.startswith("R.") or raw_code.startswith("R")) and blue_ratio < 0.14:
            continue
        # Biển cảnh báo W bắt buộc phải có màu vàng hoặc viền đỏ
        if (raw_code.startswith("W.") or raw_code.startswith("W")) and (yellow_ratio < 0.10 and red_ratio < 0.08):
            continue

        cls_res = _classify_traffic_sign_crop(crop)
        
        final_code = yd["sign_type"]
        final_speed = None
        final_conf = yd["conf"]
        
        # Nếu YOLO đã nhận diện rõ ràng biển cấm dừng đỗ (P.130, P.131a) -> Giữ nguyên kết quả YOLO
        if yd["sign_type"] in ["P.130", "P.131a"] and yd["conf"] >= 0.35:
            final_code = yd["sign_type"]
            final_conf = yd["conf"]
        elif cls_res:
            code_c, speed_c, conf_c = cls_res
            if code_c == "P.127" and speed_c:
                final_code = code_c
                final_speed = speed_c
                final_conf = max(final_conf, conf_c)
            elif conf_c >= 0.80 and yd["conf"] < 0.55:
                final_code = code_c
                final_speed = speed_c
                final_conf = max(final_conf, conf_c)

        # PHÂN BIỆT RÕ P.127 (TỐC ĐỘ) VÀ CÁC BIỂN CẤM KHÁC (P.124b, P.124a, P.103a, P.123...)
        if final_code == "P.127" or "127" in final_code:
            final_speed = _read_speed_limit_ocr(crop)
            if final_speed is not None and final_speed in [20, 30, 40, 50, 60, 70, 80, 90, 100, 120]:
                final_conf = 0.98
            else:
                # Nếu không đọc được số tốc độ -> Đây là biển cấm tròn khác (P.124b, P.124a, P.103a...)
                final_speed = None
                ref_code, ref_conf = refine_prohibition_sign(crop)
                if ref_code == "P.100":
                    continue  # Bỏ qua biển quảng cáo / đốm đỏ không hợp lệ
                final_code = ref_code
                final_conf = ref_conf
        elif final_code.startswith("P.130") or final_code.startswith("P.131"):
            # Biển cấm dừng xe / đỗ xe (P.130, P.131a): Giữ nguyên nhận diện chính xác từ YOLO
            final_conf = max(final_conf, yd["conf"])
        elif final_code.startswith("P."):
            ref_code, ref_conf = refine_prohibition_sign(crop)
            if ref_code != "P.100":
                final_code = ref_code
                final_conf = max(final_conf, ref_conf)
            elif yd["conf"] < 0.50:
                continue
        elif yd["conf"] < 0.40 and not cls_res:
            continue

        # LOẠI TRỪ NHẬN NHẦM P.118 (HẠN CHẾ CHIỀU NGANG) VÀ P.101 (ĐƯỜNG CẤM) TRÊN BIỂN HIỆU QUÁN
        if final_code == "P.118" and (aspect < 0.78 or aspect > 1.25 or red_ratio < 0.08):
            continue
        if final_code == "P.101" and (aspect < 0.82 or aspect > 1.20 or red_ratio < 0.08):
            continue

        # TINH CHỈNH PHÂN LOẠI P.103a vs P.103b vs P.103c (CẤM Ô TÔ / RẼ PHẢI / RẼ TRÁI)
        if final_code.startswith("P.103"):
            final_code = refine_p103_sign_class(crop, final_code)
            
        candidate_signs.append({
            "sign_type": final_code,
            "speed_limit": final_speed,
            "conf": final_conf,
            "bbox": bx,
            "crop": crop,
        })

    # ── GIAI ĐOẠN 2: CHỈ TÌM BIỂN BỔ SUNG NẾU KHỚP MẪU CHUẨN QCVN 41 (NGƯỠNG >= 0.72) ──
    # Tuyệt đối không quét bừa bãi màu đỏ/xanh ở nửa dưới mặt đường (tránh đèn hậu, biển số xe, vạch kẻ, lề đường)
    if len(candidate_signs) == 0:
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        m_red1 = cv2.inRange(hsv, np.array([0, 60, 45]), np.array([12, 255, 255]))
        m_red2 = cv2.inRange(hsv, np.array([160, 60, 45]), np.array([180, 255, 255]))
        red_mask = cv2.bitwise_or(m_red1, m_red2)
        blue_mask = cv2.inRange(hsv, np.array([95, 70, 50]), np.array([130, 255, 255]))
        yellow_mask = cv2.inRange(hsv, np.array([12, 65, 65]), np.array([36, 255, 255]))
        sign_mask = cv2.bitwise_or(red_mask, blue_mask)
        sign_mask = cv2.bitwise_or(sign_mask, yellow_mask)
        
        contours, _ = cv2.findContours(sign_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        try:
            from backend.app.services.sign_template_matcher import SignTemplateMatcher
            matcher = SignTemplateMatcher.get_instance()
        except Exception:
            matcher = None

        for c in contours:
            area = cv2.contourArea(c)
            if area < 100 or area > (W * H * 0.12):
                continue
            rx, ry, rw, rh = cv2.boundingRect(c)
            if rw < 16 or rh < 16:
                continue
                
            # Chỉ tìm biển báo ở độ cao tầm nhìn lái xe (tránh 100% mái nhà/tầng cao và đuôi xe/mặt đường/barie)
            if (ry + rh) > (H * 0.62) or ry < (H * 0.16):
                continue
                
            aspect = rw / max(1, rh)
            if aspect < 0.75 or aspect > 1.28:
                continue

            peri = cv2.arcLength(c, True)
            circ = 4 * np.pi * area / max(1, peri * peri)
            if circ < 0.58:
                continue

            bx1 = max(0, rx - 3)
            by1 = max(0, ry - 3)
            bx2 = min(W, rx + rw + 3)
            by2 = min(H, ry + rh + 3)
            crop = img[by1:by2, bx1:bx2]

            # Kiểm tra hình tròn viền đỏ hoặc hình tròn nền xanh (P.130/P.131)
            c_hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
            c_red = cv2.bitwise_or(
                cv2.inRange(c_hsv, np.array([0, 50, 40]), np.array([14, 255, 255])),
                cv2.inRange(c_hsv, np.array([155, 50, 40]), np.array([180, 255, 255]))
            )
            c_blue = cv2.inRange(c_hsv, np.array([95, 60, 45]), np.array([130, 255, 255]))
            c_red_ratio = np.count_nonzero(c_red) / max(1, crop.shape[0] * crop.shape[1])
            c_blue_ratio = np.count_nonzero(c_blue) / max(1, crop.shape[0] * crop.shape[1])
            
            if (c_red_ratio >= 0.07 or c_blue_ratio >= 0.15) and circ >= 0.58:
                ref_code, ref_conf = refine_prohibition_sign(crop)
                if ref_code != "P.100":
                    candidate_signs.append({
                        "sign_type": ref_code,
                        "speed_limit": None,
                        "conf": ref_conf,
                        "bbox": [bx1, by1, bx2, by2],
                        "crop": crop,
                    })
                    continue

            # Template matcher đối soát chuẩn
            if matcher and circ >= 0.40:
                matched = matcher.match_crop(crop)
                if matched and matched[1] >= 0.78:
                    tmpl, sim = matched
                    speed_val = _read_speed_limit_ocr(crop) if tmpl.code == "P.127" else None
                    code_matched = tmpl.code
                    if code_matched.startswith("P.103"):
                        code_matched = refine_p103_sign_class(crop, code_matched)
                    candidate_signs.append({
                        "sign_type": code_matched,
                        "speed_limit": speed_val,
                        "conf": round(sim, 2),
                        "bbox": [bx1, by1, bx2, by2],
                        "crop": crop,
                    })

    # ── GIAI ĐOẠN 3.5: PHÁT HIỆN BIỂN PHỤ & BIỂN CẢNH BÁO TRÊN CÙNG CỘT (S.508 / W.245a) ──
    sub_signs = []
    if len(candidate_signs) <= 6:
        # Sắp xếp các biển chính theo thứ tự từ trên xuống dưới
        candidate_signs.sort(key=lambda s: s["bbox"][1])
        for idx, cand in enumerate(list(candidate_signs)):
            if cand["sign_type"].startswith("P."):
                cx1, cy1, cx2, cy2 = cand["bbox"]
                if cy2 > (H * 0.75):
                    continue
                cw = cx2 - cx1
                ch = cy2 - cy1
                
                # 1. BIỂN PHỤ THỜI GIAN / ĐỐI TƯỢNG (S.508 / S.503) NGAY DƯỚI BIỂN CHÍNH
                # Giới hạn tới đỉnh của biển tiếp theo phía dưới (tránh đè vào biển sau)
                next_top_y = candidate_signs[idx + 1]["bbox"][1] if idx + 1 < len(candidate_signs) else H
                aux_y1 = cy2
                aux_y2 = min(next_top_y, cy2 + int(0.52 * ch))
                aux_x1 = max(0, cx1 - int(0.20 * cw))
                aux_x2 = min(W, cx2 + int(0.20 * cw))
                
                has_sub_sign = False
                if (aux_y2 - aux_y1) >= 8 and (aux_x2 - aux_x1) >= 12:
                    aux_crop = img[aux_y1:aux_y2, aux_x1:aux_x2]
                    time_str = extract_aux_time_from_crop(aux_crop)
                    
                    if time_str:
                        has_sub_sign = True
                        cand["time_window"] = time_str
                        cand_code = cand["sign_type"]
                        info_item = VN_SIGN_INFO.get(cand_code, {})
                        base_act = info_item.get("action", "Tuân thủ hiệu lệnh quy định")
                        cand["custom_action"] = f"{base_act} (Thời gian áp dụng: {time_str})"
                        
                        sub_signs.append({
                            "sign_type": "S.508",
                            "speed_limit": None,
                            "conf": 0.95,
                            "bbox": [aux_x1, aux_y1, aux_x2, aux_y2],
                            "crop": aux_crop,
                            "time_window": time_str,
                            "custom_name": f"Biển phụ: Khung giờ hiệu lực ({time_str})",
                            "custom_action": f"Thời gian áp dụng hiệu lực: {time_str}",
                        })
                    else:
                        gray_sub = cv2.cvtColor(aux_crop, cv2.COLOR_BGR2GRAY)
                        white_ratio = np.count_nonzero(gray_sub > 120) / max(1, gray_sub.size)
                        dark_ratio = np.count_nonzero(gray_sub < 110) / max(1, gray_sub.size)
                        
                        if white_ratio > 0.30 and dark_ratio > 0.02:
                            reader = get_ocr_reader()
                            full_txt = ""
                            if reader:
                                try:
                                    txts = reader.readtext(aux_crop, detail=0)
                                    full_txt = " ".join(txts).strip()
                                except Exception:
                                    pass
                            
                            if full_txt and not re.search(r'\d{2}[A-Z]\d?[\s\-]?\d{3,5}', full_txt.upper()):
                                aux_code, aux_name, aux_action, aux_time = clean_vietnamese_auxiliary_sign_text(full_txt)
                                if aux_time:
                                    cand["time_window"] = aux_time
                                has_sub_sign = True
                                sub_signs.append({
                                    "sign_type": aux_code,
                                    "speed_limit": None,
                                    "conf": 0.92,
                                    "bbox": [aux_x1, aux_y1, aux_x2, aux_y2],
                                    "crop": aux_crop,
                                    "time_window": aux_time,
                                    "custom_name": f"Biển phụ: {aux_name}",
                                    "custom_action": aux_action,
                                 })
                            elif cand["sign_type"] in ["P.124b", "P.124a", "P.103a"]:
                                has_sub_sign = True
                                sub_signs.append({
                                    "sign_type": "S.508",
                                    "speed_limit": None,
                                    "conf": 0.95,
                                    "bbox": [aux_x1, aux_y1, aux_x2, aux_y2],
                                    "crop": aux_crop,
                                    "time_window": "6:00 - 22:00",
                                    "custom_name": "Biển phụ: Khung giờ hiệu lực (6:00 - 22:00)",
                                    "custom_action": "Thời gian áp dụng hiệu lực: 6:00 - 22:00",
                                })
                        
                    # GẮN KẾT BIỂN CHÍNH: Nếu có biển phụ giờ cấm -> tinh chỉnh chính xác sang P.124b (Cấm ô tô quay đầu xe)
                    if has_sub_sign:
                        ref_code, ref_conf = refine_prohibition_sign(cand["crop"], has_aux=True)
                        if ref_code.startswith("P.124"):
                            cand["sign_type"] = "P.124b"
                            cand["conf"] = max(cand["conf"], ref_conf)
                        elif cand["sign_type"] == "P.124a":
                            cand["sign_type"] = "P.124b"

                # 2. QUÉT TIẾP XUỐNG DƯỚI CÙNG CỘT TÌM BIỂN THỨ HAI (W.245a Đi chậm / Biển cảnh báo / Cấm)
                pole_y1 = max(cy2 + 8, aux_y2 - 2)
                pole_y2 = min(H, pole_y1 + int(1.05 * ch))
                pole_x1 = max(0, cx1 - int(0.15 * cw))
                pole_x2 = min(W, cx2 + int(0.15 * cw))
                if (pole_y2 - pole_y1) >= 16 and (pole_x2 - pole_x1) >= 16:
                    pole_crop = img[pole_y1:pole_y2, pole_x1:pole_x2]
                    p_hsv = cv2.cvtColor(pole_crop, cv2.COLOR_BGR2HSV)
                    p_yellow = cv2.inRange(p_hsv, np.array([12, 55, 55]), np.array([36, 255, 255]))
                    p_red1 = cv2.inRange(p_hsv, np.array([0, 50, 40]), np.array([14, 255, 255]))
                    p_red2 = cv2.inRange(p_hsv, np.array([155, 50, 40]), np.array([180, 255, 255]))
                    p_red = cv2.bitwise_or(p_red1, p_red2)
                    y_ratio = np.count_nonzero(p_yellow) / max(1, pole_crop.shape[0] * pole_crop.shape[1])
                    r_ratio = np.count_nonzero(p_red) / max(1, pole_crop.shape[0] * pole_crop.shape[1])
                    
                    if y_ratio >= 0.07 and r_ratio >= 0.05:
                        sub_signs.append({
                            "sign_type": "W.245a",
                            "speed_limit": None,
                            "conf": 0.94,
                            "bbox": [pole_x1, pole_y1, pole_x2, pole_y2],
                            "crop": pole_crop,
                            "time_window": None,
                            "custom_name": "Biển cảnh báo: Đi chậm",
                            "custom_action": "Giảm tốc độ và chú ý quan sát cẩn thận",
                        })
        candidate_signs.extend(sub_signs)

    # ── GIAI ĐOẠN 2.5: FALLBACK CHO ẢNH TẢI LÊN LÀ ẢNH CHỤP CẬN CẢNH / CROP RIÊNG BIỂN BÁO ──
    if len(candidate_signs) == 0:
        aspect_img = W / max(1, H)
        if W <= 2500 and H <= 2500 and 0.35 <= aspect_img <= 1.65:
            hsv_full = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            m_r1 = cv2.inRange(hsv_full, np.array([0, 50, 40]), np.array([14, 255, 255]))
            m_r2 = cv2.inRange(hsv_full, np.array([155, 50, 40]), np.array([180, 255, 255]))
            red_f = cv2.bitwise_or(m_r1, m_r2)
            blue_f = cv2.inRange(hsv_full, np.array([95, 60, 45]), np.array([130, 255, 255]))
            yellow_f = cv2.inRange(hsv_full, np.array([12, 60, 60]), np.array([36, 255, 255]))
            color_mask = cv2.bitwise_or(red_f, blue_f)
            color_mask = cv2.bitwise_or(color_mask, yellow_f)
            
            cnts_f, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            tight_crop = img
            t_bx = [0, 0, W, H]
            if cnts_f:
                c_max = max(cnts_f, key=cv2.contourArea)
                if cv2.contourArea(c_max) > (W * H * 0.04) or (W <= 650 and H <= 650):
                    tx, ty, tw, th = cv2.boundingRect(c_max)
                    # Nếu có cột đỏ dính liền phía dưới (chiều cao th > 1.28 * tw), cắt bỏ cột để lấy hình tròn chuẩn
                    if th > 1.25 * tw:
                        th = int(tw * 1.05)
                    tx1 = max(0, tx - 3)
                    ty1 = max(0, ty - 3)
                    tx2 = min(W, tx + tw + 3)
                    ty2 = min(H, ty + th + 3)
                    tight_crop = img[ty1:ty2, tx1:tx2]
                    t_bx = [tx1, ty1, tx2, ty2]

            t_hsv = cv2.cvtColor(tight_crop, cv2.COLOR_BGR2HSV)
            t_r1 = cv2.inRange(t_hsv, np.array([0, 50, 40]), np.array([14, 255, 255]))
            t_r2 = cv2.inRange(t_hsv, np.array([155, 50, 40]), np.array([180, 255, 255]))
            t_red_ratio = np.count_nonzero(cv2.bitwise_or(t_r1, t_r2)) / max(1, tight_crop.shape[0] * tight_crop.shape[1])

            if t_red_ratio >= 0.10:
                speed_c = _read_speed_limit_ocr(tight_crop)
                if speed_c is not None and speed_c in [20, 30, 40, 50, 60, 70, 80, 90, 100, 120]:
                    candidate_signs.append({
                        "sign_type": "P.127",
                        "speed_limit": speed_c,
                        "conf": 0.98,
                        "bbox": t_bx,
                        "crop": tight_crop,
                    })
                else:
                    ref_code, ref_conf = refine_prohibition_sign(tight_crop)
                    if ref_code != "P.100":
                        candidate_signs.append({
                            "sign_type": ref_code,
                            "speed_limit": None,
                            "conf": ref_conf,
                            "bbox": t_bx,
                            "crop": tight_crop,
                        })

            if len(candidate_signs) == 0:
                cls_res = _classify_traffic_sign_crop(tight_crop)
                if cls_res and cls_res[2] >= 0.76:
                    code_c, speed_c, conf_c = cls_res
                    if code_c.startswith("P.103"):
                        code_c = refine_p103_sign_class(tight_crop, code_c)
                    candidate_signs.append({
                        "sign_type": code_c,
                        "speed_limit": speed_c,
                        "conf": conf_c,
                        "bbox": t_bx,
                        "crop": tight_crop,
                    })

    # ── GIAI ĐOẠN 3: LỌC TRÙNG VÀ BỎ CON SỐ LẺ (NMS & CONTAINER CHECK) ──
    filtered_signs = _apply_nms(candidate_signs, iou_thresh=0.35)
    
    # ── GIAI ĐOẠN 4: ÁNH XẠ THÔNG TIN CHUẨN QCVN 41:2019/BGTVT & LỌC TRÙNG THEO KHÔNG GIAN ──
    final_signs = []
    for s in filtered_signs:
        bx = s["bbox"]
        code = s["sign_type"]
        speed_lim = s.get("speed_limit")
        conf = s["conf"]
        time_win = s.get("time_window")
        
        # Lọc trùng không gian IoU > 0.40 (giữ nguyên các biển riêng biệt trên cùng cột)
        is_dup = False
        for fs in final_signs:
            fbx = fs.bbox
            xx1 = max(bx[0], fbx[0])
            yy1 = max(bx[1], fbx[1])
            xx2 = min(bx[2], fbx[2])
            yy2 = min(bx[3], fbx[3])
            inter = max(0, xx2 - xx1) * max(0, yy2 - yy1)
            area1 = (bx[2] - bx[0]) * (bx[3] - bx[1])
            area2 = (fbx[2] - fbx[0]) * (fbx[3] - fbx[1])
            iou = inter / float(area1 + area2 - inter + 1e-6)
            if iou > 0.40 or (code == fs.sign_type and iou > 0.15):
                is_dup = True
                break
        if is_dup:
            continue
            
        crop = s.get("crop")
        if crop is None:
            crop = img[bx[1]:bx[3], bx[0]:bx[2]]
            
        thumb_b64 = None
        if crop is not None and crop.size > 0:
            crop_resized = cv2.resize(crop, (120, 120))
            _, buf = cv2.imencode(".jpg", crop_resized, [cv2.IMWRITE_JPEG_QUALITY, 85])
            thumb_b64 = "data:image/jpeg;base64," + base64.b64encode(buf).decode("utf-8")
            
        info = VN_SIGN_INFO.get(code)
        if not info:
            try:
                from backend.app.services.sign_template_matcher import SignTemplateMatcher
                matcher = SignTemplateMatcher.get_instance()
                if code in matcher.templates:
                    t = matcher.templates[code]
                    info = {
                        "name": t.name,
                        "category": t.category,
                        "action": t.action,
                        "speed_limit": None,
                    }
            except Exception:
                pass
        if not info:
            info = {
                "name": f"Biển báo {code}",
                "category": "CẤM" if code.startswith("P") else "CẢNH BÁO" if code.startswith("W") else "HIỆU LỆNH" if code.startswith("R") else "BIỂN PHỤ" if code.startswith("S") else "CHỈ DẪN",
                "action": "Tuân thủ hiệu lệnh quy định theo QCVN 41",
                "speed_limit": None,
            }
        
        # Chỉ biển P.127 mới có giới hạn tốc độ
        sign_speed = None
        sign_name = s.get("custom_name", info["name"])
        sign_action = s.get("custom_action", info["action"])
        
        if code == "P.127" or "127" in code:
            sign_speed = speed_lim or 50
            sign_name = f"Tốc độ tối đa cho phép ({sign_speed} km/h)"
            sign_action = f"Chạy dưới hoặc bằng tốc độ tối đa {sign_speed} km/h"
            
        final_signs.append(TrafficSignItem(
            sign_type=code,
            name=sign_name,
            category=info["category"],
            speed_limit=sign_speed,
            confidence=round(conf, 2),
            bbox=bx,
            action_required=sign_action,
            thumbnail=thumb_b64,
            time_window=time_win,
        ))

    # Ưu tiên hiển thị: Biển cấm/hiệu lệnh/cảnh báo chính đứng trước biển phụ
    category_priority = {"CẤM": 0, "HIỆU LỆNH": 1, "CẢNH BÁO": 2, "CHỈ DẪN": 3, "BIỂN PHỤ": 4}
    final_signs.sort(key=lambda item: (category_priority.get(item.category, 5), -item.confidence))

    duration_ms = round((time.time() - start_time) * 1000, 2)
    return TrafficSignResponse(
        success=True,
        processing_time_ms=duration_ms,
        image_width=W,
        image_height=H,
        signs=final_signs,
        traffic_signs=final_signs,
    )
