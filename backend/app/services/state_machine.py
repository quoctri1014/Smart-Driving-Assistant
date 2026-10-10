from typing import Tuple, Optional
from fastapi import HTTPException, status

# Hợp lệ các trạng thái
REVIEW_STATUSES = {"PENDING_REVIEW", "NEEDS_EVIDENCE", "CONFIRMED", "FALSE_POSITIVE"}
RESOLUTION_STATUSES = {"OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"}

# Ma trận chuyển trạng thái Review Status hợp lệ
# Format: {Current_Status: {Allowed_Target_Statuses}}
VALID_REVIEW_TRANSITIONS = {
    "PENDING_REVIEW": {"CONFIRMED", "FALSE_POSITIVE", "NEEDS_EVIDENCE"},
    "NEEDS_EVIDENCE": {"CONFIRMED", "FALSE_POSITIVE", "PENDING_REVIEW"},
    "CONFIRMED": {"CONFIRMED"}, # Chỉ thay đổi resolution_status, hoặc REOPEN
    "FALSE_POSITIVE": {"PENDING_REVIEW"}, # Chỉ được chuyển về PENDING_REVIEW thông qua action REOPEN
}

# Ma trận chuyển trạng thái Resolution Status hợp lệ
VALID_RESOLUTION_TRANSITIONS = {
    "OPEN": {"IN_PROGRESS", "RESOLVED", "CLOSED"},
    "IN_PROGRESS": {"RESOLVED", "CLOSED", "OPEN"},
    "RESOLVED": {"CLOSED", "OPEN"},
    "CLOSED": {"OPEN"}, # Reopen
}

def validate_and_compute_transition(
    current_review_status: str,
    current_resolution_status: str,
    action: str,
    note: Optional[str] = None
) -> Tuple[str, str]:
    """
    Central State Machine Transition Validator.
    Xác thực quy trình thẩm định sự cố vi phạm (Human-in-the-loop):
    - Đảm bảo logic chuyển đổi trạng thái hợp lệ.
    - Validate độ dài ghi chú giải trình (Bắt buộc >= 5 ký tự đối với FALSE_POSITIVE và RESOLVE).
    - Trả về: (new_review_status, new_resolution_status) hoặc raise HTTPException 409/422.
    """
    cur_rev = current_review_status.upper() if current_review_status else "PENDING_REVIEW"
    cur_res = current_resolution_status.upper() if current_resolution_status else "OPEN"
    act = action.upper().strip()

    # 1. Map Action sang Target States
    if act == "CONFIRM":
        target_rev = "CONFIRMED"
        target_res = "OPEN" if cur_res == "CLOSED" else cur_res
    elif act == "FALSE_POSITIVE":
        target_rev = "FALSE_POSITIVE"
        target_res = "CLOSED"
    elif act in ("NEED_EVIDENCE", "NEEDS_EVIDENCE"):
        target_rev = "NEEDS_EVIDENCE"
        target_res = cur_res
    elif act == "RESOLVE":
        target_rev = "CONFIRMED"
        target_res = "RESOLVED"
    elif act == "IN_PROGRESS":
        target_rev = "CONFIRMED"
        target_res = "IN_PROGRESS"
    elif act == "CLOSE":
        target_rev = cur_rev
        target_res = "CLOSED"
    elif act == "REOPEN":
        target_rev = "PENDING_REVIEW"
        target_res = "OPEN"
    else:
        # Fallback cho action dạng tên trạng thái trực tiếp
        if act in REVIEW_STATUSES:
            target_rev = act
            target_res = cur_res
        elif act in RESOLUTION_STATUSES:
            target_rev = cur_rev
            target_res = act
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Thao tác không hợp lệ: '{action}'"
            )

    # 2. Validation Notes bắt buộc
    clean_note = (note or "").strip()
    if act in ("FALSE_POSITIVE", "RESOLVE") and len(clean_note) < 5:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Bắt buộc phải nhập ghi chú giải trình tối thiểu 5 ký tự cho thao tác này."
        )

    # 3. Validate chuyển đổi Review Status
    if target_rev != cur_rev:
        allowed_targets = VALID_REVIEW_TRANSITIONS.get(cur_rev, set())
        if target_rev not in allowed_targets and act != "REOPEN":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Chuyển đổi trạng thái thẩm định không hợp lệ: Không thể chuyển từ '{cur_rev}' sang '{target_rev}' trực tiếp."
            )

    # 4. Validate chuyển đổi Resolution Status
    if target_res != cur_res:
        allowed_res_targets = VALID_RESOLUTION_TRANSITIONS.get(cur_res, set())
        if target_res not in allowed_res_targets and act != "REOPEN":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Chuyển đổi trạng thái xử lý không hợp lệ: Không thể chuyển từ '{cur_res}' sang '{target_res}'."
            )

    return target_rev, target_res
