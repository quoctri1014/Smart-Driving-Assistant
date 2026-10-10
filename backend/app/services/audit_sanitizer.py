import json
from typing import Dict, Any, Optional, Tuple, List, Union

SENSITIVE_SUBSTRINGS = {
    "password", "password_hash", "hashed_password", "token", "access_token",
    "refresh_token", "jwt", "secret", "api_key", "secret_key", "credential",
    "credentials", "auth_header", "pin", "otp", "authorization", "cookie",
    "session", "camera_password", "camera_token", "database_password",
    "client_secret", "private_key"
}

def is_sensitive_key(key: str) -> bool:
    low = key.lower()
    return any(sub in low for sub in SENSITIVE_SUBSTRINGS)

def sanitize_data(data: Any) -> Any:
    """
    Khử trùng đệ quy (Recursive Sanitizer) cho Dict, List và Primitive types.
    Ẩn hoàn toàn mật khẩu, tokens, JWT, cookies, secrets ở mọi cấp độ lồng nhau.
    """
    if data is None:
        return None
    if isinstance(data, dict):
        sanitized = {}
        for k, v in data.items():
            if is_sensitive_key(str(k)):
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = sanitize_data(v)
        return sanitized
    elif isinstance(data, list):
        return [sanitize_data(item) for item in data]
    elif isinstance(data, (set, tuple)):
        return [sanitize_data(item) for item in data]
    return data

def sanitize_dict(data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if data is None:
        return None
    if not isinstance(data, dict):
        return sanitize_data(data)
    return sanitize_data(data)

def compute_diff(old_obj: Optional[Dict[str, Any]], new_obj: Optional[Dict[str, Any]]) -> Tuple[Optional[str], Optional[str]]:
    """
    Chỉ lưu các trường có sự thay đổi (Diff-only) sau khi đã khử trùng dữ liệu nhạy cảm.
    """
    sanitized_old = sanitize_dict(old_obj) or {}
    sanitized_new = sanitize_dict(new_obj) or {}

    old_diff = {}
    new_diff = {}

    all_keys = set(sanitized_old.keys()).union(set(sanitized_new.keys()))
    for key in all_keys:
        val_old = sanitized_old.get(key)
        val_new = sanitized_new.get(key)
        if val_old != val_new:
            if val_old is not None:
                old_diff[key] = val_old
            if val_new is not None:
                new_diff[key] = val_new

    old_str = json.dumps(old_diff, ensure_ascii=False) if old_diff else None
    new_str = json.dumps(new_diff, ensure_ascii=False) if new_diff else None
    return old_str, new_str
