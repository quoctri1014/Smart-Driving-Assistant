import os
import sys
import re
import cv2
import json
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_PAGE_2 = os.path.join(BASE_DIR, 'pdf_page_hi_2.png')
PDF_PAGE_1 = os.path.join(BASE_DIR, 'pdf_page_hi_1.png')
PDF_PAGE_3 = os.path.join(BASE_DIR, 'pdf_page_hi_3.png')
PDF_PAGE_4 = os.path.join(BASE_DIR, 'pdf_page_hi_4.png')

OUTPUT_DIR = os.path.join(BASE_DIR, 'backend', 'app', 'assets', 'qcvn_signs')
WEB_SIGNS_DIR = os.path.join(BASE_DIR, 'web-app', 'public', 'signs')
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(WEB_SIGNS_DIR, exist_ok=True)

# ── 1. MAPPING ĐẦY ĐỦ CHUẨN QCVN 41:2019 / 01-06-2020 CHO TRANG 2 (BIỂN BÁO CẤM & HẾT CẤM) ──
PAGE2_MAPPING = [
    # Row 1
    {"code": "P.101", "name": "Đường cấm", "category": "CẤM", "action": "Cấm tất cả các loại phương tiện đi lại cả hai hướng"},
    {"code": "P.102", "name": "Cấm đi ngược chiều", "category": "CẤM", "action": "Cấm tất cả các loại xe đi vào theo chiều đặt biển"},
    {"code": "P.112", "name": "Cấm người đi bộ", "category": "CẤM", "action": "Cấm người đi bộ qua lại trên đoạn đường này"},
    {"code": "P.110a", "name": "Cấm xe đạp", "category": "CẤM", "action": "Cấm xe đạp đi vào đoạn đường này"},
    {"code": "P.111a", "name": "Cấm xe gắn máy", "category": "CẤM", "action": "Cấm các loại xe gắn máy đi vào"},
    {"code": "P.104", "name": "Cấm xe mô tô 2-3 bánh", "category": "CẤM", "action": "Cấm các loại xe mô tô hai bánh và ba bánh"},
    {"code": "P.103a", "name": "Cấm xe ô tô", "category": "CẤM", "action": "Cấm tất cả các loại xe cơ giới từ 3 bánh trở lên đi vào"},
    # Row 2
    {"code": "P.105", "name": "Cấm ô tô và xe máy", "category": "CẤM", "action": "Cấm các loại xe cơ giới và xe mô tô"},
    {"code": "P.107a", "name": "Cấm xe ô tô khách", "category": "CẤM", "action": "Cấm ô tô chở khách từ 9 chỗ trở lên"},
    {"code": "P.106a", "name": "Cấm xe ô tô tải", "category": "CẤM", "action": "Cấm các loại xe ô tô tải trừ xe ưu tiên"},
    {"code": "P.107b", "name": "Cấm xe ô tô khách và ô tô tải", "category": "CẤM", "action": "Cấm cả ô tô tải và ô tô khách"},
    {"code": "P.107c", "name": "Cấm xe ô tô taxi", "category": "CẤM", "action": "Cấm các loại xe taxi lưu thông"},
    {"code": "P.108a", "name": "Cấm xe sơ-mi rơ-moóc", "category": "CẤM", "action": "Cấm các loại xe đầu kéo kéo sơ-mi rơ-moóc"},
    {"code": "P.108", "name": "Cấm xe kéo rơ-moóc", "category": "CẤM", "action": "Cấm các loại xe cơ giới kéo theo rơ-moóc"},
    # Row 3
    {"code": "P.109", "name": "Cấm máy kéo", "category": "CẤM", "action": "Cấm các loại máy kéo bánh hơi và bánh xích"},
    {"code": "P.113", "name": "Cấm xe công nông", "category": "CẤM", "action": "Cấm xe công nông và xe tự chế"},
    {"code": "P.114", "name": "Cấm xe súc vật kéo", "category": "CẤM", "action": "Cấm súc vật vận tải hoặc kéo xe"},
    {"code": "P.111b", "name": "Cấm xe ba bánh có động cơ", "category": "CẤM", "action": "Cấm các loại xe lam, xe lôi, xích lô máy"},
    {"code": "P.111c", "name": "Cấm xe ba bánh không có động cơ", "category": "CẤM", "action": "Cấm xe xích lô và xe ba gác đạp"},
    {"code": "P.111d", "name": "Cấm xe lôi", "category": "CẤM", "action": "Cấm các loại xe lôi đạp và kéo"},
    {"code": "P.110b", "name": "Cấm xe chở hàng nguy hiểm", "category": "CẤM", "action": "Cấm các xe vận chuyển chất cháy, nổ, độc hại"},
    # Row 4
    {"code": "P.123a", "name": "Cấm rẽ trái", "category": "CẤM", "action": "Cấm các loại phương tiện cơ giới và thô sơ rẽ trái (được phép quay đầu)"},
    {"code": "P.103c", "name": "Cấm xe ô tô rẽ trái", "category": "CẤM", "action": "Cấm các loại xe cơ giới rẽ trái"},
    {"code": "P.123b", "name": "Cấm rẽ phải", "category": "CẤM", "action": "Cấm các loại phương tiện cơ giới và thô sơ rẽ phải"},
    {"code": "P.103b", "name": "Cấm xe ô tô rẽ phải", "category": "CẤM", "action": "Cấm các loại xe cơ giới rẽ phải"},
    {"code": "P.124a", "name": "Cấm quay đầu xe", "category": "CẤM", "action": "Cấm tất cả phương tiện quay đầu xe theo kiểu chữ U"},
    {"code": "P.124b", "name": "Cấm ô tô quay đầu xe", "category": "CẤM", "action": "Cấm xe ô tô quay đầu xe theo kiểu chữ U"},
    {"code": "P.124b_alt", "name": "Cấm ô tô quay đầu xe (mẫu 2)", "category": "CẤM", "action": "Cấm xe ô tô quay đầu xe"},
    # Row 5
    {"code": "P.124b_alt2", "name": "Cấm ô tô quay đầu xe (mẫu 3)", "category": "CẤM", "action": "Cấm xe ô tô quay đầu xe"},
    {"code": "P.124c", "name": "Cấm rẽ trái và quay đầu xe", "category": "CẤM", "action": "Cấm các phương tiện rẽ trái đồng thời cấm quay đầu xe"},
    {"code": "P.124e", "name": "Cấm ô tô rẽ trái và quay đầu xe", "category": "CẤM", "action": "Cấm ô tô rẽ trái đồng thời cấm quay đầu xe"},
    {"code": "P.124d", "name": "Cấm rẽ phải và quay đầu xe", "category": "CẤM", "action": "Cấm các phương tiện rẽ phải đồng thời cấm quay đầu xe"},
    {"code": "P.124f", "name": "Cấm ô tô rẽ phải và quay đầu xe", "category": "CẤM", "action": "Cấm ô tô rẽ phải đồng thời cấm quay đầu xe"},
    {"code": "P.117", "name": "Hạn chế chiều cao xe", "category": "CẤM", "action": "Cấm các xe có chiều cao vượt quá chỉ số ghi trên biển"},
    {"code": "P.118", "name": "Hạn chế chiều ngang xe", "category": "CẤM", "action": "Cấm các xe có chiều ngang vượt quá mức ghi trên biển"},
    # Row 6
    {"code": "P.115", "name": "Hạn chế tải trọng toàn bộ xe", "category": "CẤM", "action": "Cấm xe có trọng lượng toàn bộ vượt quá số tấn ghi trên biển"},
    {"code": "P.116", "name": "Hạn chế tải trọng trên trục xe", "category": "CẤM", "action": "Cấm xe có tải trọng phân bổ trên trục vượt quá chỉ số ghi trên biển"},
    {"code": "P.119", "name": "Hạn chế chiều dài xe", "category": "CẤM", "action": "Cấm các xe có chiều dài tổng thể vượt quá mức ghi trên biển"},
    {"code": "P.120", "name": "Hạn chế chiều dài xe kéo moóc", "category": "CẤM", "action": "Cấm đoàn xe kéo moóc có tổng chiều dài vượt quá mức ghi trên biển"},
    {"code": "P.121", "name": "Cự ly tối thiểu giữa hai xe", "category": "CẤM", "action": "Giữ khoảng cách tối thiểu với xe đi trước theo chỉ số mét"},
    {"code": "P.125", "name": "Cấm vượt", "category": "CẤM", "action": "Cấm tất cả các loại xe cơ giới vượt nhau"},
    {"code": "P.126", "name": "Cấm ô tô tải vượt", "category": "CẤM", "action": "Cấm các loại ô tô tải có khối lượng chuyên chở vượt xe cơ giới khác"},
    # Row 7
    {"code": "P.127", "name": "Tốc độ tối đa cho phép", "category": "CẤM", "action": "Chạy dưới hoặc bằng tốc độ tối đa ghi trên mặt biển", "speed_limit": 50},
    {"code": "P.127b", "name": "Tốc độ tối đa ban đêm", "category": "CẤM", "action": "Chạy dưới hoặc bằng tốc độ quy định vào khung giờ ban đêm", "speed_limit": 70},
    {"code": "P.128", "name": "Cấm sử dụng còi", "category": "CẤM", "action": "Không được bấm còi trong phạm vi có hiệu lực"},
    {"code": "P.130", "name": "Cấm dừng xe và đỗ xe", "category": "CẤM", "action": "Cấm các phương tiện dừng xe và đỗ xe ở đoạn đường này"},
    {"code": "P.131a", "name": "Cấm đỗ xe", "category": "CẤM", "action": "Cấm tất cả các phương tiện đỗ xe ở đoạn đường đặt biển"},
    {"code": "P.131b", "name": "Cấm đỗ xe ngày lẻ", "category": "CẤM", "action": "Cấm đỗ xe vào các ngày lẻ trong tháng"},
    {"code": "P.131c", "name": "Cấm đỗ xe ngày chẵn", "category": "CẤM", "action": "Cấm đỗ xe vào các ngày chẵn trong tháng"},
    # Row 8
    {"code": "P.132", "name": "Nhường đường cho xe ngược chiều", "category": "CẤM", "action": "Nhường đường cho xe cơ giới đi ngược chiều qua đoạn đường hẹp"},
    {"code": "P.127c", "name": "Tốc độ tối đa theo phương tiện trên từng làn đường", "category": "CẤM", "action": "Tuân thủ tốc độ tối đa theo từng làn xe quy định"},
    {"code": "P.127d", "name": "Tốc độ tối đa theo từng làn đường", "category": "CẤM", "action": "Tuân thủ tốc độ tối đa theo từng làn đường chỉ định"},
    {"code": "DP.135", "name": "Hết tất cả các lệnh cấm", "category": "HIỆU LỆNH", "action": "Đã hết hiệu lực của các biển cấm trước đó"},
    {"code": "DP.133", "name": "Hết cấm vượt", "category": "HIỆU LỆNH", "action": "Được phép vượt xe trở lại bình thường"},
    {"code": "DP.134", "name": "Hết hạn chế tốc độ tối đa", "category": "HIỆU LỆNH", "action": "Hết hiệu lực của biển hạn chế tốc độ trước đó"},
    {"code": "DP.134b", "name": "Hết hạn chế tốc độ theo biển ghép", "category": "HIỆU LỆNH", "action": "Hết hiệu lực hạn chế tốc độ ghép"},
]

# ── 2. MAPPING CHUẨN TRANG 1 (BIỂN BÁO NGUY HIỂM NHÓM W) ──
PAGE1_MAPPING = [
    {"code": "W.205a", "name": "Đường giao nhau cùng mức (ngã tư)", "category": "CẢNH BÁO", "action": "Giao nhau cùng mức các tuyến đường cùng cấp"},
    {"code": "W.205b", "name": "Đường giao nhau nhánh bên phải", "category": "CẢNH BÁO", "action": "Giao nhau nhánh đường cùng cấp bên phải"},
    {"code": "W.205c", "name": "Đường giao nhau nhánh bên trái", "category": "CẢNH BÁO", "action": "Giao nhau nhánh đường cùng cấp bên trái"},
    {"code": "W.207a", "name": "Giao nhau với đường không ưu tiên", "category": "CẢNH BÁO", "action": "Đang đi trên đường ưu tiên qua nơi giao nhau"},
    {"code": "W.207b", "name": "Giao nhau đường không ưu tiên bên phải", "category": "CẢNH BÁO", "action": "Có nhánh đường phụ nhập vào từ bên phải"},
    {"code": "W.207c", "name": "Giao nhau đường không ưu tiên bên trái", "category": "CẢNH BÁO", "action": "Có nhánh đường phụ nhập vào từ bên trái"},
    {"code": "W.208", "name": "Giao nhau với đường ưu tiên", "category": "CẢNH BÁO", "action": "Nhường đường cho xe trên tuyến đường ưu tiên"},
    {"code": "W.209", "name": "Nơi giao nhau có tín hiệu đèn", "category": "CẢNH BÁO", "action": "Chuẩn bị tới nơi giao nhau có đèn giao thông"},
    {"code": "W.226", "name": "Đường người đi xe đạp cắt ngang", "category": "CẢNH BÁO", "action": "Chú ý người đi xe đạp qua đường"},
    {"code": "W.224", "name": "Đường người đi bộ cắt ngang", "category": "CẢNH BÁO", "action": "Giảm tốc độ, chú ý nhường đường người đi bộ"},
    {"code": "W.225", "name": "Trẻ em qua đường", "category": "CẢNH BÁO", "action": "Khu vực trường học hoặc sân chơi trẻ em, đi chậm"},
    {"code": "W.204", "name": "Đường hai chiều", "category": "CẢNH BÁO", "action": "Đoạn đường lưu thông theo cả 2 chiều ngược nhau"},
    {"code": "W.234", "name": "Giao nhau với đường hai chiều", "category": "CẢNH BÁO", "action": "Sắp giao nhau với tuyến đường hai chiều"},
    {"code": "W.235", "name": "Đường đôi", "category": "CẢNH BÁO", "action": "Bắt đầu đoạn đường đôi có dải phân cách giữa"},
    {"code": "W.236", "name": "Kết thúc đường đôi", "category": "CẢNH BÁO", "action": "Hết đoạn đường đôi, chú ý làn xe ngược chiều"},
    {"code": "W.216", "name": "Cầu vồng", "category": "CẢNH BÁO", "action": "Đoạn cầu vồng dốc gồ ghề hạn chế tầm nhìn"},
    {"code": "W.217", "name": "Cửa chui", "category": "CẢNH BÁO", "action": "Sắp qua cửa chui hẹp, chú ý chiều cao xe"},
    {"code": "W.218", "name": "Đường hầm", "category": "CẢNH BÁO", "action": "Sắp vào hầm đường bộ, bật đèn xe"},
    {"code": "W.238", "name": "Đường cao tốc phía trước", "category": "CẢNH BÁO", "action": "Sắp vào đường cao tốc"},
    {"code": "W.246", "name": "Ùn tắc giao thông", "category": "CẢNH BÁO", "action": "Đoạn đường thường xuyên ùn tắc"},
    {"code": "W.222", "name": "Đường trơn", "category": "CẢNH BÁO", "action": "Mặt đường trơn trượt, giảm tốc độ tránh phanh gấp"},
    {"code": "W.244", "name": "Đoạn đường hay xảy ra tai nạn", "category": "CẢNH BÁO", "action": "Đi chậm và chú ý quan sát đặc biệt"},
    {"code": "W.230", "name": "Gia súc", "category": "CẢNH BÁO", "action": "Gia súc thường qua đường bất ngờ"},
    {"code": "W.231", "name": "Gió ngang", "category": "CẢNH BÁO", "action": "Gió thổi ngang mạnh nguy hiểm, giữ vững tay lái"},
    {"code": "W.232", "name": "Nền đường yếu", "category": "CẢNH BÁO", "action": "Đoạn đường có nền đất yếu dễ sụt lún"},
    {"code": "W.229", "name": "Sỏi đá bắn lên", "category": "CẢNH BÁO", "action": "Mặt đường rải sỏi đá dăm, giữ cự ly xa xe trước"},
    {"code": "W.239", "name": "Đường cáp điện ở phía trên", "category": "CẢNH BÁO", "action": "Chú ý tĩnh không đường dây điện cao thế"},
    {"code": "W.215", "name": "Bến phà", "category": "CẢNH BÁO", "action": "Sắp đến bến phà, đi chậm theo hướng dẫn"},
    {"code": "W.228", "name": "Đá lở", "category": "CẢNH BÁO", "action": "Nguy cơ đất đá sạt lở từ taluy dương"},
    {"code": "W.227", "name": "Công trường thi công", "category": "CẢNH BÁO", "action": "Đoạn đường đang sửa chữa hoặc thi công, giảm tốc"},
    {"code": "W.240", "name": "Lề đường nguy hiểm", "category": "CẢNH BÁO", "action": "Lề đường không ổn định dễ trượt bánh"},
    {"code": "W.212", "name": "Kè, vực sâu phía trước", "category": "CẢNH BÁO", "action": "Bờ kè hoặc bờ vực phía trước"},
    {"code": "W.213", "name": "Kè, vực sâu bên trái", "category": "CẢNH BÁO", "action": "Bờ vực hoặc mặt nước bên trái"},
    {"code": "W.214", "name": "Kè, vực sâu bên phải", "category": "CẢNH BÁO", "action": "Bờ vực hoặc mặt nước bên phải"},
    {"code": "W.219", "name": "Dốc xuống nguy hiểm", "category": "CẢNH BÁO", "action": "Đoạn dốc xuống sâu nguy hiểm, đi số thấp"},
    {"code": "W.220", "name": "Dốc lên nguy hiểm", "category": "CẢNH BÁO", "action": "Đoạn dốc lên cao, chú ý không vượt ẩu"},
    {"code": "W.221b", "name": "Đường có gờ giảm tốc", "category": "CẢNH BÁO", "action": "Mặt đường có gờ giảm tốc, đi chậm lại"},
    {"code": "W.221a", "name": "Đường có ổ gà lồi lõm", "category": "CẢNH BÁO", "action": "Mặt đường xấu, lồi lõm nhiều ổ gà"},
    {"code": "W.211", "name": "Cầu hẹp", "category": "CẢNH BÁO", "action": "Đoạn cầu hẹp một làn xe"},
    {"code": "W.211b", "name": "Cầu tạm", "category": "CẢNH BÁO", "action": "Đoạn cầu tạm có tải trọng giới hạn"},
    {"code": "W.213b", "name": "Cầu quay - cầu cất", "category": "CẢNH BÁO", "action": "Cầu quay hoặc cầu cất nhịp thông thuyền"},
    {"code": "W.201a", "name": "Chỗ ngoặt nguy hiểm vòng bên trái", "category": "CẢNH BÁO", "action": "Đoạn đường cong gấp nguy hiểm về phía bên trái"},
    {"code": "W.201b", "name": "Chỗ ngoặt nguy hiểm vòng bên phải", "category": "CẢNH BÁO", "action": "Đoạn đường cong gấp nguy hiểm về phía bên phải"},
    {"code": "W.203a", "name": "Đường bị hẹp cả hai bên", "category": "CẢNH BÁO", "action": "Mặt đường bị hẹp đột ngột từ cả hai phía"},
    {"code": "W.203b", "name": "Đường bị hẹp về phía trái", "category": "CẢNH BÁO", "action": "Mặt đường bị hẹp đột ngột về phía bên trái"},
    {"code": "W.203c", "name": "Đường bị hẹp về phía phải", "category": "CẢNH BÁO", "action": "Mặt đường bị hẹp đột ngột về phía bên phải"},
    {"code": "W.202a", "name": "Nhiều chỗ ngoặt nguy hiểm liên tiếp sang trái", "category": "CẢNH BÁO", "action": "Nhiều khúc cua gấp liên tiếp, cua đầu sang trái"},
    {"code": "W.202b", "name": "Nhiều chỗ ngoặt nguy hiểm liên tiếp sang phải", "category": "CẢNH BÁO", "action": "Nhiều khúc cua gấp liên tiếp, cua đầu sang phải"},
    {"code": "W.206", "name": "Giao nhau chạy theo vòng xuyến", "category": "CẢNH BÁO", "action": "Nơi giao nhau có đảo giao thông vòng xuyến"},
    {"code": "W.242", "name": "Giao nhau với đường tàu điện", "category": "CẢNH BÁO", "action": "Giao cắt với tuyến tàu điện"},
    {"code": "W.210", "name": "Giao nhau với đường sắt có rào chắn", "category": "CẢNH BÁO", "action": "Đường sắt giao nhau có rào chắn tự động"},
    {"code": "W.211a", "name": "Giao nhau với đường sắt không rào chắn", "category": "CẢNH BÁO", "action": "Đường sắt giao nhau không rào chắn, dừng lại quan sát"},
    {"code": "W.243a", "name": "Nơi đường sắt giao vuông góc", "category": "CẢNH BÁO", "action": "Nơi đường sắt giao cắt vuông góc với đường bộ"},
    {"code": "W.243b", "name": "Nơi đường sắt giao không vuông góc", "category": "CẢNH BÁO", "action": "Nơi đường sắt giao cắt chéo với đường bộ"},
]

# ── 3. MAPPING CHUẨN TRANG 3 (BIỂN HIỆU LỆNH R & CHỈ DẪN I) ──
PAGE3_MAPPING = [
    {"code": "R.301a", "name": "Các xe chỉ được đi thẳng", "category": "HIỆU LỆNH", "action": "Các phương tiện chỉ được phép đi thẳng"},
    {"code": "R.301b", "name": "Các xe chỉ được rẽ phải", "category": "HIỆU LỆNH", "action": "Các phương tiện chỉ được phép rẽ sang phải"},
    {"code": "R.301c", "name": "Các xe chỉ được rẽ trái", "category": "HIỆU LỆNH", "action": "Các phương tiện chỉ được phép rẽ sang trái"},
    {"code": "R.301d", "name": "Các xe chỉ được rẽ phải (ngã ba/tư)", "category": "HIỆU LỆNH", "action": "Chỉ được phép rẽ phải ở phạm vi ngã ba, ngã tư"},
    {"code": "R.301e", "name": "Các xe chỉ được đi thẳng và rẽ trái", "category": "HIỆU LỆNH", "action": "Chỉ được phép đi thẳng hoặc rẽ trái"},
    {"code": "R.301f", "name": "Các xe chỉ được đi thẳng và rẽ phải", "category": "HIỆU LỆNH", "action": "Chỉ được phép đi thẳng hoặc rẽ phải"},
    {"code": "R.301h", "name": "Các xe rẽ trái và rẽ phải", "category": "HIỆU LỆNH", "action": "Chỉ được rẽ trái hoặc rẽ phải"},
    {"code": "R.302a", "name": "Hướng phải đi vòng sang phải", "category": "HIỆU LỆNH", "action": "Phải đi vòng tránh chướng ngại vật sang bên phải"},
    {"code": "R.302b", "name": "Hướng phải đi vòng sang trái", "category": "HIỆU LỆNH", "action": "Phải đi vòng tránh chướng ngại vật sang bên trái"},
    {"code": "R.303", "name": "Nơi giao nhau chạy theo vòng xuyến", "category": "HIỆU LỆNH", "action": "Chạy vòng quanh đảo an toàn theo chiều mũi tên"},
    {"code": "R.304", "name": "Đường dành cho xe thô sơ", "category": "HIỆU LỆNH", "action": "Đoạn đường chỉ dành riêng cho xe thô sơ"},
    {"code": "R.305", "name": "Đường dành cho người đi bộ", "category": "HIỆU LỆNH", "action": "Đoạn đường chỉ dành riêng cho người đi bộ"},
    {"code": "R.306", "name": "Tốc độ tối thiểu cho phép", "category": "HIỆU LỆNH", "action": "Chạy với tốc độ lớn hơn hoặc bằng tốc độ ghi trên biển", "speed_limit": 60},
    {"code": "R.307", "name": "Hết hạn chế tốc độ tối thiểu", "category": "HIỆU LỆNH", "action": "Hết hiệu lực tốc độ tối thiểu"},
    {"code": "R.403a", "name": "Đường dành cho ô tô", "category": "HIỆU LỆNH", "action": "Bắt đầu đoạn đường dành riêng cho xe ô tô"},
    {"code": "R.403b", "name": "Đường dành cho ô tô và xe máy", "category": "HIỆU LỆNH", "action": "Đoạn đường dành riêng cho ô tô và xe máy"},
    {"code": "R.404a", "name": "Hết đoạn đường dành cho ô tô", "category": "HIỆU LỆNH", "action": "Hết đoạn đường dành riêng cho ô tô"},
    {"code": "R.404b", "name": "Hết đoạn đường dành cho ô tô và xe máy", "category": "HIỆU LỆNH", "action": "Hết đoạn đường dành riêng cho ô tô và xe máy"},
    {"code": "R.411", "name": "Hướng đi trên mỗi làn đường theo vạch kẻ", "category": "HIỆU LỆNH", "action": "Tuân thủ hướng đi quy định trên từng làn đường"},
    {"code": "R.412a", "name": "Làn đường dành cho ô tô khách", "category": "HIỆU LỆNH", "action": "Làn đường dành riêng cho ô tô khách"},
    {"code": "R.412b", "name": "Làn đường dành cho ô tô con", "category": "HIỆU LỆNH", "action": "Làn đường dành riêng cho ô tô con"},
    {"code": "R.412c", "name": "Làn đường dành cho ô tô tải", "category": "HIỆU LỆNH", "action": "Làn đường dành riêng cho ô tô tải"},
    {"code": "R.412d", "name": "Làn đường dành cho xe máy", "category": "HIỆU LỆNH", "action": "Làn đường dành riêng cho xe máy"},
    {"code": "R.415", "name": "Biển gộp làn đường theo phương tiện", "category": "HIỆU LỆNH", "action": "Đi đúng làn đường theo loại phương tiện quy định"},
    {"code": "R.420", "name": "Bắt đầu khu đông dân cư", "category": "HIỆU LỆNH", "action": "Bắt đầu khu vực đông dân cư, giảm tốc độ"},
    {"code": "R.421", "name": "Hết khu đông dân cư", "category": "HIỆU LỆNH", "action": "Hết khu vực đông dân cư"},
    {"code": "I.401", "name": "Bắt đầu đường ưu tiên", "category": "CHỈ DẪN", "action": "Đoạn đường được quyền ưu tiên qua nơi giao nhau"},
    {"code": "I.402", "name": "Hết đoạn đường ưu tiên", "category": "CHỈ DẪN", "action": "Hết quyền ưu tiên qua nơi giao nhau"},
    {"code": "I.406", "name": "Được ưu tiên qua đường hẹp", "category": "CHỈ DẪN", "action": "Được quyền ưu tiên qua đoạn đường hẹp"},
    {"code": "I.407a", "name": "Đường một chiều", "category": "CHỈ DẪN", "action": "Đoạn đường chỉ lưu thông theo một chiều quy định"},
    {"code": "I.408a", "name": "Nơi đỗ xe", "category": "CHỈ DẪN", "action": "Khu vực được phép đỗ xe ô tô"},
    {"code": "I.408b", "name": "Nơi đỗ xe một phần trên hè phố", "category": "CHỈ DẪN", "action": "Được phép đỗ một phần bánh xe trên hè"},
    {"code": "I.409", "name": "Chỗ quay xe", "category": "CHỈ DẪN", "action": "Vị trí được phép quay đầu xe an toàn"},
    {"code": "I.410", "name": "Khu vực quay xe", "category": "CHỈ DẪN", "action": "Khu vực rộng cho phép các xe quay đầu"},
]


def extract_page2_signs():
    print(">>> Extracting Page 2 signs (Biển báo cấm QCVN 41)...")
    img = cv2.imread(PDF_PAGE_2)
    if img is None:
        print("Cannot read", PDF_PAGE_2)
        return []

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    r1 = cv2.inRange(hsv, np.array([0, 70, 70]), np.array([12, 255, 255]))
    r2 = cv2.inRange(hsv, np.array([160, 70, 70]), np.array([180, 255, 255]))
    red = cv2.bitwise_or(r1, r2)
    blue = cv2.inRange(hsv, np.array([95, 70, 70]), np.array([130, 255, 255]))
    yellow = cv2.inRange(hsv, np.array([15, 70, 70]), np.array([35, 255, 255]))
    combined = cv2.bitwise_or(red, cv2.bitwise_or(blue, yellow))
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    closed = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if 100 < w < 350 and 100 < h < 350 and y > 400:
            boxes.append((x, y, w, h))

    boxes = sorted(boxes, key=lambda b: (b[1] // 100, b[0]))
    print(f"Page 2: Found {len(boxes)} sign bounding boxes.")

    results = []
    for i, box in enumerate(boxes):
        if i >= len(PAGE2_MAPPING):
            break
        meta = PAGE2_MAPPING[i]
        x, y, w, h = box
        pad = 8
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(img.shape[1], x + w + pad)
        y2 = min(img.shape[0], y + h + pad)
        crop = img[y1:y2, x1:x2]
        crop_std = cv2.resize(crop, (160, 160), interpolation=cv2.INTER_AREA)

        fname = f"{meta['code'].replace('.', '_')}.png"
        out_path = os.path.join(OUTPUT_DIR, fname)
        web_path = os.path.join(WEB_SIGNS_DIR, fname)
        cv2.imwrite(out_path, crop_std)
        cv2.imwrite(web_path, crop_std)

        item = {
            "code": meta["code"],
            "name": meta["name"],
            "category": meta["category"],
            "action": meta["action"],
            "speed_limit": meta.get("speed_limit"),
            "img_filename": fname,
            "page": 2,
        }
        results.append(item)
        print(f"  [P2] {meta['code']}: {meta['name']} -> {fname}")
    return results


def extract_page1_signs():
    print(">>> Extracting Page 1 signs (Biển cảnh báo nguy hiểm QCVN 41)...")
    img = cv2.imread(PDF_PAGE_1)
    if img is None:
        return []

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    r1 = cv2.inRange(hsv, np.array([0, 70, 70]), np.array([12, 255, 255]))
    r2 = cv2.inRange(hsv, np.array([160, 70, 70]), np.array([180, 255, 255]))
    red = cv2.bitwise_or(r1, r2)
    yellow = cv2.inRange(hsv, np.array([15, 70, 70]), np.array([35, 255, 255]))
    combined = cv2.bitwise_or(red, yellow)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    closed = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if 90 < w < 350 and 90 < h < 350 and y > 600:
            boxes.append((x, y, w, h))

    boxes = sorted(boxes, key=lambda b: (b[1] // 100, b[0]))
    print(f"Page 1: Found {len(boxes)} sign bounding boxes.")

    results = []
    for i, box in enumerate(boxes):
        if i >= len(PAGE1_MAPPING):
            break
        meta = PAGE1_MAPPING[i]
        x, y, w, h = box
        pad = 8
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(img.shape[1], x + w + pad)
        y2 = min(img.shape[0], y + h + pad)
        crop = img[y1:y2, x1:x2]
        crop_std = cv2.resize(crop, (160, 160), interpolation=cv2.INTER_AREA)

        fname = f"{meta['code'].replace('.', '_')}.png"
        out_path = os.path.join(OUTPUT_DIR, fname)
        web_path = os.path.join(WEB_SIGNS_DIR, fname)
        cv2.imwrite(out_path, crop_std)
        cv2.imwrite(web_path, crop_std)

        item = {
            "code": meta["code"],
            "name": meta["name"],
            "category": meta["category"],
            "action": meta["action"],
            "speed_limit": meta.get("speed_limit"),
            "img_filename": fname,
            "page": 1,
        }
        results.append(item)
        print(f"  [P1] {meta['code']}: {meta['name']} -> {fname}")
    return results


def extract_page3_signs():
    print(">>> Extracting Page 3 signs (Biển hiệu lệnh & Chỉ dẫn QCVN 41)...")
    img = cv2.imread(PDF_PAGE_3)
    if img is None:
        return []

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    blue = cv2.inRange(hsv, np.array([95, 60, 60]), np.array([135, 255, 255]))
    r1 = cv2.inRange(hsv, np.array([0, 70, 70]), np.array([12, 255, 255]))
    r2 = cv2.inRange(hsv, np.array([160, 70, 70]), np.array([180, 255, 255]))
    red = cv2.bitwise_or(r1, r2)
    combined = cv2.bitwise_or(blue, red)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    closed = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if 70 < w < 350 and 70 < h < 350 and y > 400:
            boxes.append((x, y, w, h))

    boxes = sorted(boxes, key=lambda b: (b[1] // 80, b[0]))
    print(f"Page 3: Found {len(boxes)} sign bounding boxes.")

    results = []
    for i, box in enumerate(boxes):
        if i >= len(PAGE3_MAPPING):
            break
        meta = PAGE3_MAPPING[i]
        x, y, w, h = box
        pad = 6
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(img.shape[1], x + w + pad)
        y2 = min(img.shape[0], y + h + pad)
        crop = img[y1:y2, x1:x2]
        crop_std = cv2.resize(crop, (160, 160), interpolation=cv2.INTER_AREA)

        fname = f"{meta['code'].replace('.', '_')}.png"
        out_path = os.path.join(OUTPUT_DIR, fname)
        web_path = os.path.join(WEB_SIGNS_DIR, fname)
        cv2.imwrite(out_path, crop_std)
        cv2.imwrite(web_path, crop_std)

        item = {
            "code": meta["code"],
            "name": meta["name"],
            "category": meta["category"],
            "action": meta["action"],
            "speed_limit": meta.get("speed_limit"),
            "img_filename": fname,
            "page": 3,
        }
        results.append(item)
        print(f"  [P3] {meta['code']}: {meta['name']} -> {fname}")
    return results


def main():
    p2 = extract_page2_signs()
    p1 = extract_page1_signs()
    p3 = extract_page3_signs()
    all_signs = p2 + p1 + p3

    catalog_path = os.path.join(OUTPUT_DIR, "qcvn_signs_catalog.json")
    with open(catalog_path, "w", encoding="utf-8") as f:
        json.dump(all_signs, f, ensure_ascii=False, indent=2)

    web_catalog = os.path.join(BASE_DIR, "web-app", "public", "signs", "qcvn_signs_catalog.json")
    with open(web_catalog, "w", encoding="utf-8") as f:
        json.dump(all_signs, f, ensure_ascii=False, indent=2)

    print(f"\n=======================================================")
    print(f"SUCCESS! Extracted and cataloged {len(all_signs)} QCVN 41:2019 traffic signs!")
    print(f"Catalog saved to: {catalog_path}")
    print(f"Web assets saved to: {web_catalog}")
    print(f"=======================================================")


if __name__ == '__main__':
    main()
