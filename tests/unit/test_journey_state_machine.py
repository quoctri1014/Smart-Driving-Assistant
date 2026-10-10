import pytest
import pytest_asyncio
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from backend.app.database.base import Base
from backend.app.models_db.organization import Organization
from backend.app.models_db.driver import Driver
from backend.app.models_db.vehicle import Vehicle
from backend.app.models_db.journey import Journey
from backend.app.crud import journey_crud


@pytest_asyncio.fixture
async def async_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        # Seed test organization, dispatcher, driver, vehicle
        org = Organization(id=1, name="Logistics Test Co")
        session.add(org)

        dispatcher = Driver(
            id=10,
            company_id=1,
            email="dispatcher@test.com",
            password_hash="fakehash",
            full_name="Nguyễn Văn Điều Độ",
            role="FLEET_DISPATCHER"
        )
        driver1 = Driver(
            id=20,
            company_id=1,
            email="driver1@test.com",
            password_hash="fakehash",
            full_name="Trần Văn Lái Xe",
            role="FLEET_DRIVER",
            safety_score=100.0
        )
        vehicle1 = Vehicle(
            id=100,
            company_id=1,
            license_plate="29A-999.99",
            vehicle_type="truck"
        )
        session.add_all([dispatcher, driver1, vehicle1])
        await session.commit()
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_journey_lifecycle_state_machine(async_db: AsyncSession):
    # 1. Dispatcher tạo chuyến (PLANNED)
    journey = await journey_crud.create_journey(
        db=async_db,
        company_id=1,
        dispatcher_id=10,
        vehicle_id=100,
        driver_id=20,
        title="Chuyến Hà Nội - Hải Phòng",
        start_location="Hà Nội",
        destination="Hải Phòng"
    )
    assert journey.id is not None
    assert journey.status == "PLANNED"
    assert journey.checklist_status == "PENDING"
    assert journey.safety_score == 100.0

    # 2. Không thể bắt đầu chuyến trực tiếp khi chưa nộp checklist
    with pytest.raises(ValueError, match="chưa hoàn thành checklist"):
        await journey_crud.start_journey(
            db=async_db,
            journey_id=journey.id,
            company_id=1,
            driver_id=20
        )

    # 3. Tài xế nộp checklist không đạt (ví dụ phanh hỏng: brakes=False)
    failed_checklist = {
        "roadCamera": True,
        "cabinCamera": True,
        "brakes": False,
        "tires": True,
        "lights": True
    }
    updated_jrn = await journey_crud.submit_pre_trip_checklist(
        db=async_db,
        journey_id=journey.id,
        company_id=1,
        driver_id=20,
        checklist_dict=failed_checklist
    )
    assert updated_jrn.status == "CHECKLIST"
    assert updated_jrn.checklist_status == "FAILED"

    # Thử khởi hành với checklist FAILED -> Phải bị chặn
    with pytest.raises(ValueError, match="Checklist an toàn xe chưa đạt chuẩn PASSED"):
        await journey_crud.start_journey(
            db=async_db,
            journey_id=journey.id,
            company_id=1,
            driver_id=20
        )

    # 4. Tài xế khắc phục và nộp lại checklist đạt chuẩn (PASSED)
    passed_checklist = {
        "roadCamera": True,
        "cabinCamera": True,
        "brakes": True,
        "tires": True,
        "lights": True,
        "documents": True
    }
    updated_jrn = await journey_crud.submit_pre_trip_checklist(
        db=async_db,
        journey_id=journey.id,
        company_id=1,
        driver_id=20,
        checklist_dict=passed_checklist
    )
    assert updated_jrn.checklist_status == "PASSED"

    # 5. Khởi hành chuyến đi (ACTIVE)
    active_jrn = await journey_crud.start_journey(
        db=async_db,
        journey_id=journey.id,
        company_id=1,
        driver_id=20
    )
    assert active_jrn.status == "ACTIVE"
    assert active_jrn.actual_start_time is not None
    assert active_jrn.session_id is not None  # Đã liên kết telemetry session

    # 6. Chặn double active: Không thể tạo & chạy chuyến thứ 2 cùng lúc cho cùng tài xế
    second_jrn = await journey_crud.create_journey(
        db=async_db,
        company_id=1,
        dispatcher_id=10,
        vehicle_id=100,
        driver_id=20,
        title="Chuyến trùng lặp"
    )
    await journey_crud.submit_pre_trip_checklist(
        db=async_db,
        journey_id=second_jrn.id,
        company_id=1,
        driver_id=20,
        checklist_dict=passed_checklist
    )
    with pytest.raises(ValueError, match="Tài xế đang có chuyến"):
        await journey_crud.start_journey(
            db=async_db,
            journey_id=second_jrn.id,
            company_id=1,
            driver_id=20
        )

    # 7. Hoàn thành chuyến (COMPLETED)
    completed_jrn = await journey_crud.complete_journey(
        db=async_db,
        journey_id=active_jrn.id,
        company_id=1,
        user_id=20,
        total_distance_km=125.5,
        notes="Giao hàng thành công đúng giờ"
    )
    assert completed_jrn.status == "COMPLETED"
    assert completed_jrn.completed_at is not None
    assert completed_jrn.total_distance_km == 125.5

    # 8. Hủy chuyến chưa chạy kèm lý do (CANCELLED)
    cancelled_jrn = await journey_crud.cancel_journey(
        db=async_db,
        journey_id=second_jrn.id,
        company_id=1,
        user_id=10,
        reason="Khách hàng hủy đơn hàng"
    )
    assert cancelled_jrn.status == "CANCELLED"
    assert cancelled_jrn.cancel_reason == "Khách hàng hủy đơn hàng"
