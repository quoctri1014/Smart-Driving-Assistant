import sys
import time
from pathlib import Path
from report_builder import create_styled_document, DOCX_OUT
from report_front_matter import build_front_matter
from section_ch1_ch2 import build_chapter_1, build_chapter_2
from section_ch3_ch4 import build_chapter_3, build_chapter_4
from section_ch5_ch6 import build_chapter_5, build_chapter_6
from section_ch7_ch9 import build_chapter_7, build_chapter_8, build_chapter_9_and_appendix

def main():
    print("=" * 60)
    print("BAT DAU KHOI TAO TAI LIEU BAO CAO DO AN (TRAFFICGUARD)")
    print("=" * 60)
    
    t0 = time.time()
    doc = create_styled_document()
    
    print("[1/5] Xay dung Phan mo dau (Trang bia, Tom tat, Tu viet tat)...")
    build_front_matter(doc)
    
    print("[2/5] Xay dung Chuong 1 & Chuong 2 (Tong quan, Co so ly thuyet & Cong nghe)...")
    build_chapter_1(doc)
    build_chapter_2(doc)
    
    print("[3/5] Xay dung Chuong 3 & Chuong 4 (Thiet ke he thong & 12 Module AI Core)...")
    build_chapter_3(doc)
    build_chapter_4(doc)
    
    print("[4/5] Xay dung Chuong 5 & Chuong 6 (Backend FastAPI & Giao dien Web/Mobile)...")
    build_chapter_5(doc)
    build_chapter_6(doc)
    
    print("[5/5] Xay dung Chuong 7, 8, 9 & Phu luc (Kiem thu 90/90, Phap ly, Ket luan)...")
    build_chapter_7(doc)
    build_chapter_8(doc)
    build_chapter_9_and_appendix(doc)
    
    print(f"Luu tai lieu xuat ban tai: {DOCX_OUT}...")
    doc.save(str(DOCX_OUT))
    
    file_size_kb = DOCX_OUT.stat().st_size / 1024
    t_elapsed = time.time() - t0
    
    print("=" * 60)
    print(f"XUAT BAN THANH CONG!")
    print(f"File: {DOCX_OUT.resolve()}")
    print(f"Kich thuoc: {file_size_kb:.1f} KB")
    print(f"Thoi gian tao: {t_elapsed:.2f} giay")
    print("=" * 60)

if __name__ == '__main__':
    main()
