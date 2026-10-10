import io
from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database.session import get_db
from backend.app.models_db.driver import Driver
from backend.app.auth.dependencies import require_permission
from backend.app.services.report_generator import (
    generate_safety_summary,
    export_safety_report_excel,
    export_safety_report_pdf
)

router = APIRouter()


@router.get("/safety-summary")
@router.get("/summary")
async def get_safety_summary(
    days: int = Query(30, ge=1, le=365, description="Số ngày cần tổng hợp báo cáo"),
    current_user: Driver = Depends(require_permission("reports.view")),
    db: AsyncSession = Depends(get_db)
):
    """Báo cáo tổng hợp an toàn tuần/tháng, xu hướng vi phạm và tài xế rủi ro cao"""
    company_id = current_user.organization_id or 1
    summary = await generate_safety_summary(db=db, company_id=company_id, days=days)
    return summary


@router.get("/export/excel")
@router.get("/export")
async def download_excel_report(
    days: int = Query(30, ge=1, le=365),
    current_user: Driver = Depends(require_permission("reports.export")),
    db: AsyncSession = Depends(get_db)
):
    """Xuất báo cáo tổng quan an toàn và tài xế rủi ro cao định dạng Excel (.xlsx)"""
    company_id = current_user.organization_id or 1
    summary = await generate_safety_summary(db=db, company_id=company_id, days=days)
    excel_bytes = export_safety_report_excel(summary)

    filename = f"BaoCao_AnToan_DoiXe_{days}Ngay.xlsx"
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/export/pdf")
async def download_pdf_report(
    days: int = Query(30, ge=1, le=365),
    current_user: Driver = Depends(require_permission("reports.export")),
    db: AsyncSession = Depends(get_db)
):
    """Xuất báo cáo tổng quan an toàn định dạng PDF chuẩn doanh nghiệp (.pdf)"""
    company_id = current_user.organization_id or 1
    summary = await generate_safety_summary(db=db, company_id=company_id, days=days)
    pdf_bytes = export_safety_report_pdf(summary)

    filename = f"BaoCao_AnToan_DoiXe_{days}Ngay.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
