import os
import shutil
import json

base_dir = r"D:\Smart Driving Assistant"
src_img_dir = os.path.join(base_dir, "Bien_bao_giao_thong_Viet_Nam_md", "img")
dst_backend_dir = os.path.join(base_dir, "backend", "app", "assets", "qcvn_signs")
dst_web_dir = os.path.join(base_dir, "web-app", "public", "signs")

s_signs_meta = [
    {"code": "S.501", "name": "Phạm vi tác dụng của biển", "category": "BIỂN PHỤ", "action": "Báo chiều dài đoạn đường biển chính có hiệu lực", "img": "S_501.png"},
    {"code": "S.502", "name": "Khoảng cách đến đối tượng báo hiệu", "category": "BIỂN PHỤ", "action": "Báo khoảng cách thực tế từ vị trí đặt biển đến nơi báo hiệu", "img": "S_502.png"},
    {"code": "S.503a", "name": "Hướng tác dụng của biển", "category": "BIỂN PHỤ", "action": "Chỉ hướng tác dụng của biển chính (hai đầu mũi tên)", "img": "S_503a.png"},
    {"code": "S.504", "name": "Làn đường áp dụng", "category": "BIỂN PHỤ", "action": "Chỉ làn đường chịu hiệu lực của biển chính hoặc đèn tín hiệu", "img": "S_504.png"},
    {"code": "S.505", "name": "Loại xe chịu hiệu lực của biển chính", "category": "BIỂN PHỤ", "action": "Chỉ loại xe chịu hiệu lực của biển báo chính", "img": "S_505.png"},
    {"code": "S.506a", "name": "Hướng đường ưu tiên", "category": "BIỂN PHỤ", "action": "Chỉ hướng của đường ưu tiên tại nơi giao nhau", "img": "S_506a.png"},
    {"code": "S.507", "name": "Hướng rẽ", "category": "BIỂN PHỤ", "action": "Báo trước chỗ rẽ nguy hiểm và chỉ hướng rẽ", "img": "S_507.png"},
    {"code": "S.508", "name": "Thời gian hiệu lực", "category": "BIỂN PHỤ", "action": "Thời gian biển chính có hiệu lực trong ngày hoặc trong tuần (ví dụ: 6:00 - 22:00)", "img": "S_508.png"},
    {"code": "S.509", "name": "Thuyết minh biển chính", "category": "BIỂN PHỤ", "action": "Bổ sung nội dung thuyết minh chỉ dẫn cho biển chính", "img": "S_509.png"},
    {"code": "S.509a", "name": "Thuyết minh biển báo", "category": "BIỂN PHỤ", "action": "Giải thích bổ sung cho biển báo chính", "img": "S_509.png"},
]

for s in s_signs_meta:
    src_f = os.path.join(src_img_dir, s["img"])
    if os.path.exists(src_f):
        shutil.copy2(src_f, os.path.join(dst_backend_dir, s["img"]))
        shutil.copy2(src_f, os.path.join(dst_web_dir, s["img"]))
        if s["code"] == "S.509a":
            shutil.copy2(src_f, os.path.join(dst_backend_dir, "S_509a.png"))
            shutil.copy2(src_f, os.path.join(dst_web_dir, "S_509a.png"))
        print(f"Copied {s['code']} -> {s['img']}")

cat_path = os.path.join(dst_backend_dir, "qcvn_signs_catalog.json")
with open(cat_path, "r", encoding="utf-8") as f:
    catalog = json.load(f)

existing_codes = set(x["code"] for x in catalog)
for s in s_signs_meta:
    if s["code"] not in existing_codes:
        catalog.append({
            "code": s["code"],
            "name": s["name"],
            "category": s["category"],
            "action": s["action"],
            "speed_limit": None,
            "img_filename": s["img"] if s["code"] != "S.509a" else "S_509a.png",
            "page": 4
        })
        existing_codes.add(s["code"])

with open(cat_path, "w", encoding="utf-8") as f:
    json.dump(catalog, f, ensure_ascii=False, indent=2)

web_cat = os.path.join(dst_web_dir, "qcvn_signs_catalog.json")
with open(web_cat, "w", encoding="utf-8") as f:
    json.dump(catalog, f, ensure_ascii=False, indent=2)

print(f"Updated catalog total items: {len(catalog)}")
