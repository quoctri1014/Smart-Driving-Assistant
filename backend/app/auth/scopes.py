from enum import Enum

class DataScope(str, Enum):
    """
    Phạm vi truy cập dữ liệu (Data Scope) trong TRAFFICGUARD:
    - SELF: Chỉ dữ liệu của chính người dùng (ví dụ: ca lái, vi phạm của tài xế).
    - ASSIGNED_VEHICLE: Dữ liệu liên quan đến phương tiện được bàn giao/gán cho tài xế.
    - FLEET: Dữ liệu thuộc đội xe mà Dispatcher/Manager được phân công phụ trách.
    - BRANCH: Dữ liệu thuộc chi nhánh trực thuộc.
    - COMPANY: Toàn bộ dữ liệu trong phạm vi Doanh nghiệp (Enterprise/Organization).
    - ALL: Quyền tối thượng của System SuperAdmin (nếu có đa doanh nghiệp).
    """
    SELF = "SELF"
    ASSIGNED_VEHICLE = "ASSIGNED_VEHICLE"
    FLEET = "FLEET"
    BRANCH = "BRANCH"
    COMPANY = "COMPANY"
    ALL = "ALL"
