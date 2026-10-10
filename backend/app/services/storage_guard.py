import os
from pathlib import Path
from fastapi import HTTPException, status
from typing import Tuple

STORAGE_ROOT = os.path.abspath(os.getenv("STORAGE_PATH", "./storage"))

# Đảm bảo thư mục lưu trữ tồn tại
os.makedirs(STORAGE_ROOT, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".mp4"}
MIME_TYPE_MAP = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".mp4": "video/mp4",
}

def resolve_safe_evidence_path(raw_path: str) -> Tuple[str, str]:
    """
    Xác thực và chuyển đổi đường dẫn file bằng chứng thành canonical path an toàn.
    Chống triệt để Path Traversal (../, null bytes, symlinks, absolute path injection).
    Trả về: (canonical_absolute_path, mime_type)
    """
    if not raw_path or "\x00" in raw_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Đường dẫn tệp không hợp lệ (Null byte detected)"
        )

    # Làm sạch ký tự nguy hiểm
    clean_path = raw_path.strip().replace("\\", "/")
    
    # Bóc tách tiền tố storage nếu đã có
    if clean_path.startswith("./storage/"):
        clean_path = clean_path[len("./storage/"):]
    elif clean_path.startswith("storage/"):
        clean_path = clean_path[len("storage/"):]
    elif clean_path.startswith("./"):
        clean_path = clean_path[2:]

    # Nếu là relative path, nối với STORAGE_ROOT
    if not os.path.isabs(clean_path):
        target_path = os.path.join(STORAGE_ROOT, clean_path.lstrip("/"))
    else:
        target_path = clean_path

    # Canonicalize path (resolve symlinks, .., etc.)
    canonical_path = os.path.realpath(target_path)
    canonical_root = os.path.realpath(STORAGE_ROOT)

    # Kiểm tra path traversal: Path phải nằm hoàn toàn trong canonical_root
    if not canonical_path.startswith(canonical_root):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Từ chối truy cập: Đường dẫn tệp vi phạm giới hạn thư mục lưu trữ (Path Traversal Blocked)"
        )

    ext = Path(canonical_path).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Định dạng tệp không được hỗ trợ ({ext})"
        )

    mime_type = MIME_TYPE_MAP.get(ext, "application/octet-stream")
    return canonical_path, mime_type
