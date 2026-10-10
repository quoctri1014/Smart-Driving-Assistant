"""
voice_generator.py
------------------
Bộ sinh câu thông báo giọng đọc tiếng Việt tự nhiên, dứt khoát cho ADAS / DMS:
Quy tắc bắt buộc:
1. Câu cảnh báo nguy hiểm / khẩn cấp PHẢI NGẮN GỌN (<= 8 từ) để tài xế phản ứng tức thì trong 1 giây.
2. Không đọc chồng, hỗ trợ ngắt câu ưu tiên cao đè câu ưu tiên thấp.
"""

from typing import Optional
from backend.app.schemas.adas_event import AdasEvent


class VietnameseVoiceGenerator:
    """
    Sinh câu nhắc giọng nói chuẩn tiếng Việt <= 8 từ cho các tình huống khẩn cấp.
    """

    @staticmethod
    def generate_prompt(event: AdasEvent) -> Optional[str]:
        module = event.module
        severity = event.severity
        payload = event.payload or {}

        # 1. Va chạm khẩn cấp (TTC) - <= 8 từ
        if module == "ttc":
            if severity == "critical":
                return "Nguy hiểm! Phanh gấp, nguy cơ va chạm!"
            return "Chú ý! Xe trước đang giảm tốc nhanh!"

        # 2. Ngủ gật / DMS / Nhắm mắt kéo dài - <= 8 từ
        if module in ("drowsiness", "dms"):
            etype = getattr(event, "type", "")
            if etype == "eyes_closed_prolonged":
                return "Cảnh báo ngủ gật! Nhắm mắt quá lâu!"
            if severity == "critical":
                return "Cảnh báo ngủ gật! Dừng xe nghỉ ngay!"
            if etype == "eyes_closed_warning" or severity == "warning":
                return "Cảnh báo! Bạn đang có dấu hiệu buồn ngủ!"
            if etype == "eyes_reopened":
                return None
            return "Hãy chú ý giữ tỉnh táo khi lái xe."

        # 3. Khoảng cách an toàn - <= 8 từ
        if module == "safe_distance":
            rec_dist = payload.get("recommended_distance_m")
            if rec_dist:
                return f"Bám quá gần! Giữ khoảng cách {int(rec_dist)} mét!"
            return "Cảnh báo! Bám quá gần, hãy lùi lại!"

        # 4. Quá tốc độ - <= 8 từ
        if module == "speed":
            speed_limit = payload.get("speed_limit")
            if speed_limit:
                return f"Quá tốc độ! Giới hạn {int(speed_limit)} ki-lô-mét giờ!"
            return "Quá tốc độ! Giảm tốc độ ngay lập tức!"

        # 5. Dây an toàn - <= 8 từ
        if module == "seatbelt":
            return "Cảnh báo! Hãy cài dây an toàn ngay!"

        # 6. Biển báo giao thông - <= 8 từ
        if module == "sign":
            speed_limit = payload.get("speed_limit")
            if speed_limit:
                return f"Biển báo giới hạn tốc độ {int(speed_limit)}."
            return "Chú ý biển báo giao thông phía trước."

        # 7. Mũ bảo hiểm - <= 8 từ
        if module == "helmet":
            return "Chú ý! Người lái xe không đội mũ!"

        # 8. Thời gian lái xe liên tục - <= 8 từ
        if module == "driving_timer":
            return "Đã lái quá 4 giờ! Hãy nghỉ ngơi!"

        return None
