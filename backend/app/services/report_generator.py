"""
report_generator.py
-------------------
Tổng hợp dữ liệu báo cáo tuần/tháng, phân tích xu hướng vi phạm,
nhận diện tài xế rủi ro cao và xuất báo cáo chuyên nghiệp định dạng Excel (.xlsx) & PDF (.pdf).
"""

import io
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc

from backend.app.models_db.journey import Journey
from backend.app.models_db.violation import Violation
from backend.app.models_db.driver import Driver
from backend.app.utils.datetime_utils import utc_now

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


async def generate_safety_summary(
    db: AsyncSession,
    company_id: int,
    days: int = 30
) -> Dict[str, Any]:
    since_date = utc_now() - timedelta(days=days)

    # 1. Thống kê Chuyến đi (Journeys)
    jrn_stmt = select(Journey.status, func.count(Journey.id)).where(
        and_(Journey.company_id == company_id, Journey.created_at >= since_date)
    ).group_by(Journey.status)
    jrn_res = await db.execute(jrn_stmt)
    status_counts = dict(jrn_res.all())

    total_journeys = sum(status_counts.values())
    completed_journeys = status_counts.get("COMPLETED", 0)
    active_journeys = status_counts.get("ACTIVE", 0)
    cancelled_journeys = status_counts.get("CANCELLED", 0)
    planned_journeys = status_counts.get("PLANNED", 0)

    # 2. Thống kê Vi phạm (Violations)
    viol_stmt = select(Violation).where(
        and_(Violation.company_id == company_id, Violation.detected_at >= since_date)
    )
    viol_res = (await db.execute(viol_stmt)).scalars().all()

    total_violations = len(viol_res)
    confirmed_violations = sum(1 for v in viol_res if v.review_status == "CONFIRMED")
    false_positives = sum(1 for v in viol_res if v.review_status == "FALSE_POSITIVE")
    pending_review = sum(1 for v in viol_res if v.review_status == "PENDING_REVIEW")

    # Tỷ lệ chính xác AI dựa trên thẩm định thực tế
    reviewed_count = confirmed_violations + false_positives
    ai_precision_rate = round((confirmed_violations / reviewed_count * 100.0), 1) if reviewed_count > 0 else None

    # Phân loại theo module vi phạm
    module_counts: Dict[str, int] = {}
    severity_counts: Dict[str, int] = {"CRITICAL": 0, "WARNING": 0, "INFO": 0}
    for v in viol_res:
        v_type = v.violation_type or "unknown"
        module_counts[v_type] = module_counts.get(v_type, 0) + 1
        sev = (v.severity or "WARNING").upper()
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    # 3. Danh sách Tài xế Rủi ro cao (High-risk drivers)
    # Lấy tài xế có safety_score < 80.0 hoặc có >= 2 vi phạm CONFIRMED
    driver_stmt = select(Driver).where(
        and_(Driver.company_id == company_id, Driver.role == "FLEET_DRIVER", Driver.is_active == True)
    )
    all_drivers = (await db.execute(driver_stmt)).scalars().all()

    high_risk_drivers = []
    total_score = 0.0
    for d in all_drivers:
        d_score = getattr(d, "safety_score", 100.0) or 100.0
        total_score += d_score
        d_viols = [v for v in viol_res if v.driver_id == d.id and v.review_status == "CONFIRMED"]
        if d_score < 80.0 or len(d_viols) >= 2:
            high_risk_drivers.append({
                "driver_id": d.id,
                "full_name": d.full_name or d.email,
                "email": d.email,
                "safety_score": d_score,
                "confirmed_violations_count": len(d_viols),
                "risk_level": "RẤT CAO" if d_score < 60.0 else "TRUNG BÌNH"
            })

    high_risk_drivers.sort(key=lambda x: x["safety_score"])
    avg_fleet_score = round(total_score / len(all_drivers), 1) if all_drivers else 100.0

    return {
        "period_days": days,
        "generated_at": utc_now().strftime("%Y-%m-%d %H:%M:%S UTC"),
        "total_journeys": total_journeys,
        "completed_journeys": completed_journeys,
        "active_journeys": active_journeys,
        "cancelled_journeys": cancelled_journeys,
        "planned_journeys": planned_journeys,
        "total_violations": total_violations,
        "confirmed_violations": confirmed_violations,
        "false_positives": false_positives,
        "pending_review": pending_review,
        "ai_precision_rate": ai_precision_rate,
        "module_breakdown": module_counts,
        "severity_breakdown": severity_counts,
        "avg_fleet_safety_score": avg_fleet_score,
        "high_risk_drivers": high_risk_drivers
    }


def export_safety_report_excel(summary: Dict[str, Any]) -> bytes:
    """Sinh file Excel (.xlsx) chuyên nghiệp về an toàn và rủi ro đội xe."""
    wb = openpyxl.Workbook()

    # Sheet 1: Tổng quan an toàn
    ws1 = wb.active
    ws1.title = "Tổng Quan An Toàn"

    title_font = Font(name="Calibri", size=16, bold=True, color="1E293B")
    header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    cell_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )

    ws1.merge_cells("A1:D1")
    ws1["A1"] = "BÁO CÁO AN TOÀN ĐỘI XE & CHỈ SỐ RỦI RO (FLEET SAFETY)"
    ws1["A1"].font = title_font
    ws1["A2"] = f"Thời gian tổng hợp: {summary['period_days']} ngày gần nhất | Xuất lúc: {summary['generated_at']}"
    ws1["A2"].font = Font(size=10, italic=True, color="64748B")

    metrics = [
        ("Tổng số chuyến vận tải:", summary["total_journeys"]),
        ("Chuyến đã hoàn thành:", summary["completed_journeys"]),
        ("Chuyến đang hoạt động:", summary["active_journeys"]),
        ("Chuyến bị hủy:", summary["cancelled_journeys"]),
        ("Tổng số vi phạm phát hiện:", summary["total_violations"]),
        ("Vi phạm đã xác nhận (Confirmed):", summary["confirmed_violations"]),
        ("Dương tính giả (False Positive):", summary["false_positives"]),
        ("Độ chuẩn xác thẩm định AI (%):", f"{summary['ai_precision_rate']}%" if summary['ai_precision_rate'] is not None else "Chưa có đủ mẫu"),
        ("Điểm an toàn trung bình đội xe:", f"{summary['avg_fleet_safety_score']} / 100"),
    ]

    ws1["A4"] = "Chỉ Số Vận Hành & An Toàn"
    ws1["A4"].font = Font(size=12, bold=True)
    row_idx = 5
    for label, val in metrics:
        ws1[f"A{row_idx}"] = label
        ws1[f"B{row_idx}"] = str(val)
        ws1[f"A{row_idx}"].border = cell_border
        ws1[f"B{row_idx}"].border = cell_border
        row_idx += 1

    # Phân loại module vi phạm
    row_idx += 2
    ws1[f"A{row_idx}"] = "Phân Loại Vi Phạm Theo Module AI"
    ws1[f"A{row_idx}"].font = Font(size=12, bold=True)
    row_idx += 1
    ws1[f"A{row_idx}"] = "Module AI"
    ws1[f"B{row_idx}"] = "Số lần phát hiện"
    ws1[f"A{row_idx}"].fill = header_fill
    ws1[f"A{row_idx}"].font = header_font
    ws1[f"B{row_idx}"].fill = header_fill
    ws1[f"B{row_idx}"].font = header_font

    row_idx += 1
    for mod_name, count in summary["module_breakdown"].items():
        ws1[f"A{row_idx}"] = mod_name
        ws1[f"B{row_idx}"] = count
        ws1[f"A{row_idx}"].border = cell_border
        ws1[f"B{row_idx}"].border = cell_border
        row_idx += 1

    ws1.column_dimensions["A"].width = 38
    ws1.column_dimensions["B"].width = 25

    # Sheet 2: Tài xế rủi ro cao
    ws2 = wb.create_sheet(title="Tài Xế Rủi Ro Cao")
    ws2["A1"] = "DANH SÁCH TÀI XẾ RỦI RO CAO CẦN COUCHING"
    ws2["A1"].font = title_font

    headers = ["ID", "Họ Tên / Email", "Điểm An Toàn", "Số Vi Phạm Xác Nhận", "Mức Độ Rủi Ro"]
    for col_idx, h in enumerate(headers, start=1):
        cell = ws2.cell(row=3, column=col_idx, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.border = cell_border

    r_idx = 4
    for d in summary["high_risk_drivers"]:
        ws2.cell(row=r_idx, column=1, value=d["driver_id"]).border = cell_border
        ws2.cell(row=r_idx, column=2, value=d["full_name"]).border = cell_border
        ws2.cell(row=r_idx, column=3, value=d["safety_score"]).border = cell_border
        ws2.cell(row=r_idx, column=4, value=d["confirmed_violations_count"]).border = cell_border
        ws2.cell(row=r_idx, column=5, value=d["risk_level"]).border = cell_border
        r_idx += 1

    ws2.column_dimensions["A"].width = 10
    ws2.column_dimensions["B"].width = 32
    ws2.column_dimensions["C"].width = 18
    ws2.column_dimensions["D"].width = 25
    ws2.column_dimensions["E"].width = 20

    stream = io.BytesIO()
    wb.save(stream)
    return stream.getvalue()


def export_safety_report_pdf(summary: Dict[str, Any]) -> bytes:
    """Sinh file PDF chuẩn báo cáo doanh nghiệp."""
    stream = io.BytesIO()
    doc = SimpleDocTemplate(stream, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    elements = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=16,
        leading=20,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=6
    )
    meta_style = ParagraphStyle(
        'MetaText',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#64748B'),
        spaceAfter=15
    )
    h2_style = ParagraphStyle(
        'SectionH2',
        parent=styles['Heading2'],
        fontSize=12,
        leading=15,
        textColor=colors.HexColor('#1E293B'),
        spaceBefore=10,
        spaceAfter=8
    )

    elements.append(Paragraph("SMART DRIVING ASSISTANT - BÁO CÁO AN TOÀN ĐỘI XE", title_style))
    elements.append(Paragraph(f"Khoảng thời gian: {summary['period_days']} ngày | Thời điểm xuất: {summary['generated_at']}", meta_style))

    # Bảng chỉ số tổng quan
    elements.append(Paragraph("1. Chỉ Số Vận Hành & Vi Phạm", h2_style))
    kpi_data = [
        ["Chỉ Số", "Giá Trị", "Chỉ Số", "Giá Trị"],
        ["Tổng số chuyến:", str(summary["total_journeys"]), "Chuyến hoàn thành:", str(summary["completed_journeys"])],
        ["Tổng vi phạm:", str(summary["total_violations"]), "Vi phạm xác nhận:", str(summary["confirmed_violations"])],
        ["Dương tính giả:", str(summary["false_positives"]), "Chờ thẩm định:", str(summary["pending_review"])],
        ["Độ chuẩn xác AI:", f"{summary['ai_precision_rate']}%" if summary['ai_precision_rate'] else "N/A", "Điểm an toàn TB:", f"{summary['avg_fleet_safety_score']}/100"]
    ]

    t1 = Table(kpi_data, colWidths=[130, 130, 130, 130])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(t1)
    elements.append(Spacer(1, 15))

    # Bảng tài xế rủi ro cao
    elements.append(Paragraph("2. Danh Sách Tài Xế Rủi Ro Cao Cần Coaching", h2_style))
    driver_table_data = [["ID", "Tài Xế", "Điểm An Toàn", "Số Vi Phạm", "Mức Độ Rủi Ro"]]
    if summary["high_risk_drivers"]:
        for d in summary["high_risk_drivers"]:
            driver_table_data.append([
                str(d["driver_id"]),
                d["full_name"],
                str(d["safety_score"]),
                str(d["confirmed_violations_count"]),
                d["risk_level"]
            ])
    else:
        driver_table_data.append(["-", "Không có tài xế rủi ro cao trong kỳ", "100", "0", "AN TOÀN"])

    t2 = Table(driver_table_data, colWidths=[40, 200, 90, 90, 100])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F766E')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(t2)
    elements.append(Spacer(1, 25))

    # Chữ ký phê duyệt
    elements.append(Paragraph("3. Xác Nhận Phê Duyệt", h2_style))
    sig_data = [
        ["Người Lập Báo Cáo", "Điều Độ Viên Đội Xe", "Giám Đốc An Toàn"],
        ["\n\n\n(Ký và ghi rõ họ tên)", "\n\n\n(Ký và ghi rõ họ tên)", "\n\n\n(Ký và đóng dấu)"]
    ]
    t3 = Table(sig_data, colWidths=[170, 170, 180])
    t3.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#334155')),
    ]))
    elements.append(t3)

    doc.build(elements)
    return stream.getvalue()
