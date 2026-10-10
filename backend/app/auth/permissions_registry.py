"""
Danh mục Permission chuẩn của hệ sinh thái TRAFFICGUARD
Bao gồm định nghĩa chi tiết code, tên, phân hệ và mapping mặc định cho 3 Role:
- ENTERPRISE_ADMIN
- FLEET_DISPATCHER
- FLEET_DRIVER
"""

from typing import Dict, List, Any
from backend.app.auth.scopes import DataScope

ALL_PERMISSIONS: List[Dict[str, str]] = [
    # Dashboard
    {"code": "dashboard.view", "name": "Xem Dashboard chung", "module": "dashboard", "description": "Quyền truy cập trang Dashboard"},
    {"code": "dashboard.view_company", "name": "Xem Dashboard toàn doanh nghiệp", "module": "dashboard", "description": "Xem chỉ số an toàn và hoạt động toàn công ty"},
    {"code": "dashboard.view_fleet", "name": "Xem Dashboard theo đội xe", "module": "dashboard", "description": "Xem chỉ số an toàn đội xe được phân công"},
    {"code": "dashboard.view_self", "name": "Xem Dashboard cá nhân", "module": "dashboard", "description": "Xem điểm số và trạng thái lái xe cá nhân"},

    # Vehicle
    {"code": "vehicle.view", "name": "Xem danh sách phương tiện", "module": "vehicle", "description": "Xem danh sách xe trong phạm vi cho phép"},
    {"code": "vehicle.create", "name": "Thêm mới phương tiện", "module": "vehicle", "description": "Đăng ký xe mới vào hệ thống"},
    {"code": "vehicle.update", "name": "Cập nhật phương tiện", "module": "vehicle", "description": "Chỉnh sửa thông tin xe"},
    {"code": "vehicle.delete", "name": "Xóa phương tiện", "module": "vehicle", "description": "Gỡ bỏ xe khỏi hệ thống"},
    {"code": "vehicle.assign_driver", "name": "Phân công tài xế cho xe", "module": "vehicle", "description": "Giao nhận xe cho tài xế theo ca"},
    {"code": "vehicle.assign_device", "name": "Gán thiết bị AI cho xe", "module": "vehicle", "description": "Liên kết Camera/Box AI với xe"},

    # Driver
    {"code": "driver.view", "name": "Xem danh sách tài xế", "module": "driver", "description": "Xem danh sách hồ sơ tài xế"},
    {"code": "driver.create", "name": "Thêm mới tài xế", "module": "driver", "description": "Tạo tài khoản và hồ sơ tài xế mới"},
    {"code": "driver.update", "name": "Cập nhật hồ sơ tài xế", "module": "driver", "description": "Chỉnh sửa thông tin tài xế"},
    {"code": "driver.disable", "name": "Vô hiệu hóa tài xế", "module": "driver", "description": "Khóa hoặc đình chỉ tài khoản tài xế"},
    {"code": "driver.assign_vehicle", "name": "Gán xe cho tài xế", "module": "driver", "description": "Phân bổ phương tiện cho tài xế"},

    # Fleet
    {"code": "fleet.view", "name": "Xem danh sách đội xe", "module": "fleet", "description": "Xem danh sách các đội xe/chi nhánh"},
    {"code": "fleet.create", "name": "Tạo mới đội xe", "module": "fleet", "description": "Thêm đội xe mới trong doanh nghiệp"},
    {"code": "fleet.update", "name": "Cập nhật đội xe", "module": "fleet", "description": "Chỉnh sửa thông tin đội xe"},
    {"code": "fleet.manage_members", "name": "Quản lý thành viên đội xe", "module": "fleet", "description": "Phân bổ xe và tài xế vào đội xe"},

    # Live Monitoring
    {"code": "live.view", "name": "Xem giám sát trực tiếp", "module": "live", "description": "Truy cập giao diện Live Monitoring"},
    {"code": "live.view_road_camera", "name": "Xem camera đường đi (Road-facing)", "module": "live", "description": "Xem trực tiếp camera quan sát đường phía trước"},
    {"code": "live.view_cabin_camera", "name": "Xem camera cabin (Driver-facing)", "module": "live", "description": "Xem trực tiếp camera quan sát tài xế trong cabin"},

    # Violation & Incident
    {"code": "violation.view", "name": "Xem danh sách vi phạm", "module": "violation", "description": "Xem danh sách các lỗi vi phạm và cảnh báo an toàn"},
    {"code": "violation.review", "name": "Đánh giá duyệt vi phạm", "module": "violation", "description": "Thẩm định sự cố an toàn giao thông"},
    {"code": "violation.confirm", "name": "Xác nhận vi phạm", "module": "violation", "description": "Xác nhận vi phạm đúng và ghi nhận hồ sơ"},
    {"code": "violation.reject", "name": "Bác bỏ vi phạm (False Positive)", "module": "violation", "description": "Đánh dấu cảnh báo giả/sai của AI"},
    {"code": "violation.resolve", "name": "Xử lý hoàn tất vi phạm", "module": "violation", "description": "Ghi nhận biện pháp xử lý kỷ luật/nhắc nhở"},
    {"code": "violation.export", "name": "Xuất báo cáo vi phạm", "module": "violation", "description": "Xuất file Excel/PDF danh sách vi phạm"},

    # Evidence
    {"code": "evidence.view", "name": "Xem bằng chứng hình ảnh/video", "module": "evidence", "description": "Xem ảnh chụp snapshot và clip vi phạm"},
    {"code": "evidence.download", "name": "Tải bằng chứng hình ảnh/video", "module": "evidence", "description": "Tải tệp bằng chứng phục vụ xử lý"},

    # Journey Lifecycle & Dispatch
    {"code": "journey.view", "name": "Xem lịch sử hành trình", "module": "journey", "description": "Xem danh sách các ca và lộ trình di chuyển"},
    {"code": "journey.create", "name": "Tạo chuyến và giao xe", "module": "journey", "description": "Dispatcher tạo chuyến đi và phân công xe/tài xế"},
    {"code": "journey.checklist", "name": "Nộp/Duyệt checklist trước chuyến", "module": "journey", "description": "Thực hiện kiểm tra xe trước khi khởi hành"},
    {"code": "journey.manage", "name": "Quản lý trạng thái chuyến", "module": "journey", "description": "Chuyển trạng thái chuyến (active, completed, cancelled)"},
    {"code": "journey.export", "name": "Xuất dữ liệu hành trình", "module": "journey", "description": "Xuất nhật ký hành trình"},

    # Coaching
    {"code": "coaching.view", "name": "Xem bài tập huấn luyện", "module": "coaching", "description": "Xem danh sách bài giảng đào tạo an toàn"},
    {"code": "coaching.assign", "name": "Giao bài huấn luyện an toàn", "module": "coaching", "description": "Dispatcher giao khóa học an toàn sau vi phạm"},
    {"code": "coaching.complete", "name": "Hoàn thành bài huấn luyện", "module": "coaching", "description": "Tài xế nộp phản hồi hoàn thành khóa học"},

    # Reports
    {"code": "reports.view", "name": "Xem báo cáo xu hướng an toàn", "module": "reports", "description": "Xem tổng hợp vi phạm và tài xế rủi ro cao theo tuần/tháng"},
    {"code": "reports.export", "name": "Xuất báo cáo PDF/Excel", "module": "reports", "description": "Xuất báo cáo an toàn ra tệp PDF hoặc Excel"},

    # Analytics
    {"code": "analytics.view", "name": "Xem báo cáo phân tích", "module": "analytics", "description": "Xem biểu đồ thống kê an toàn và vận hành"},
    {"code": "analytics.export", "name": "Xuất báo cáo phân tích", "module": "analytics", "description": "Xuất báo cáo số liệu phân tích"},

    # AI Status & Config
    {"code": "ai_status.view", "name": "Xem trạng thái 12 Module AI", "module": "ai", "description": "Xem thông tin hoạt động của 12 module AI"},
    {"code": "ai_config.view", "name": "Xem cấu hình AI", "module": "ai", "description": "Xem ngưỡng độ nhạy của các bộ nhận diện AI"},
    {"code": "ai_config.update", "name": "Cập nhật cấu hình AI", "module": "ai", "description": "Điều chỉnh ngưỡng cảnh báo AI"},

    # Notification
    {"code": "notification.view", "name": "Xem thông báo cảnh báo", "module": "notification", "description": "Nhận và xem danh sách thông báo an toàn"},
    {"code": "notification.manage", "name": "Quản lý cài đặt thông báo", "module": "notification", "description": "Cấu hình luồng nhận thông báo tức thời"},

    # Audit Log
    {"code": "audit_log.view", "name": "Xem nhật ký hệ thống (Audit Log)", "module": "audit", "description": "Xem lịch sử hành động của người dùng trên hệ thống"},

    # User Management
    {"code": "user.view", "name": "Xem danh sách người dùng", "module": "user", "description": "Xem danh sách tài khoản doanh nghiệp"},
    {"code": "user.create", "name": "Tạo tài khoản người dùng", "module": "user", "description": "Tạo tài khoản Admin / Dispatcher / Manager mới"},
    {"code": "user.update", "name": "Cập nhật người dùng", "module": "user", "description": "Sửa đổi thông tin tài khoản"},
    {"code": "user.disable", "name": "Khóa tài khoản người dùng", "module": "user", "description": "Vô hiệu hóa quyền truy cập người dùng"},

    # Role & Permission Management
    {"code": "role.view", "name": "Xem danh mục quyền", "module": "role", "description": "Xem vai trò và ma trận quyền hạn"},
    {"code": "role.manage", "name": "Quản lý vai trò & quyền hạn", "module": "role", "description": "Phân bổ quyền cho các vai trò"},
]

# Mapping cho 3 Role mặc định
DEFAULT_ROLE_DEFINITIONS = {
    "ENTERPRISE_ADMIN": {
        "code": "ENTERPRISE_ADMIN",
        "name": "Quản Trị Viên Doanh Nghiệp (Enterprise Admin)",
        "description": "Toàn quyền quản trị doanh nghiệp, phân quyền, cấu hình hệ thống, xe và tài xế",
        "default_scope": DataScope.COMPANY.value,
        "permissions": [p["code"] for p in ALL_PERMISSIONS], # Toàn bộ quyền
    },
    "FLEET_DISPATCHER": {
        "code": "FLEET_DISPATCHER",
        "name": "Điều Độ Viên & Quản Lý An Toàn (Fleet Dispatcher / Safety Manager)",
        "description": "Giám sát đội xe trực tiếp, theo dõi lộ trình, thẩm định và xử lý vi phạm an toàn",
        "default_scope": DataScope.FLEET.value,
        "permissions": [
            "dashboard.view", "dashboard.view_fleet", "dashboard.view_self",
            "vehicle.view", "vehicle.update", "vehicle.assign_driver",
            "driver.view", "driver.assign_vehicle",
            "fleet.view",
            "live.view", "live.view_road_camera", "live.view_cabin_camera",
            "violation.view", "violation.review", "violation.confirm", "violation.reject", "violation.resolve", "violation.export",
            "evidence.view", "evidence.download",
            "journey.view", "journey.create", "journey.manage", "journey.export",
            "coaching.view", "coaching.assign",
            "reports.view", "reports.export",
            "analytics.view",
            "ai_status.view",
            "notification.view", "notification.manage"
        ]
    },
    "FLEET_DRIVER": {
        "code": "FLEET_DRIVER",
        "name": "Tài Xế Đội Xe (Fleet Driver)",
        "description": "Xem thông tin ca lái xe cá nhân, điểm an toàn, vi phạm cá nhân và nhận hỗ trợ lái xe",
        "default_scope": DataScope.SELF.value,
        "permissions": [
            "dashboard.view", "dashboard.view_self",
            "vehicle.view",
            "live.view",
            "violation.view",
            "evidence.view",
            "journey.view", "journey.checklist",
            "coaching.view", "coaching.complete",
            "notification.view"
        ]
    }
}
