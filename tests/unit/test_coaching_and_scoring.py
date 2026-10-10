import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from backend.app.database.base import Base
from backend.app.models_db.organization import Organization
from backend.app.models_db.driver import Driver
from backend.app.models_db.journey import Journey
from backend.app.models_db.violation import Violation
from backend.app.services.safety_scoring import deduct_driver_safety_score, restore_driver_safety_score
from backend.app.crud import coaching_crud


@pytest_asyncio.fixture
async def async_db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        org = Organization(id=1, name="Safety Co")
        session.add(org)

        dispatcher = Driver(
            id=10,
            company_id=1,
            email="dispatcher@test.com",
            password_hash="fake",
            role="FLEET_DISPATCHER"
        )
        driver = Driver(
            id=20,
            company_id=1,
            email="driver@test.com",
            password_hash="fake",
            role="FLEET_DRIVER",
            safety_score=100.0
        )
        journey = Journey(
            id=100,
            company_id=1,
            journey_code="JRN-TEST-01",
            vehicle_id=1,
            driver_id=20,
            status="ACTIVE",
            safety_score=100.0
        )
        session.add_all([dispatcher, driver, journey])
        await session.commit()
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_safety_score_deduction_and_coaching_recovery(async_db: AsyncSession):
    # 1. Ban đầu điểm tài xế là 100
    driver = (await async_db.get(Driver, 20))
    assert driver.safety_score == 100.0

    # 2. Xảy ra vi phạm WARNING (quá tốc độ) -> Trừ 5 điểm
    new_score, deduction = await deduct_driver_safety_score(
        db=async_db,
        driver_id=20,
        severity="WARNING",
        violation_type="speed_limit",
        journey_id=100
    )
    assert deduction == 5.0
    assert new_score == 95.0

    # Kiểm tra điểm hành trình cũng bị trừ tương ứng
    journey = await async_db.get(Journey, 100)
    assert journey.safety_score == 95.0

    # 3. Xảy ra vi phạm CRITICAL (buồn ngủ) -> Trừ 15 * 1.2 = 18 điểm
    new_score, deduction = await deduct_driver_safety_score(
        db=async_db,
        driver_id=20,
        severity="CRITICAL",
        violation_type="drowsy",
        journey_id=100
    )
    assert deduction == 18.0
    assert new_score == 77.0

    # 4. Dispatcher giao bài tập huấn luyện Coaching cho tài xế
    assignment = await coaching_crud.create_coaching_assignment(
        db=async_db,
        company_id=1,
        assigned_by=10,
        driver_id=20,
        title="Khóa đào tạo: Phòng chống mệt mỏi và ngủ gật khi lái xe đường dài",
        module_type="DMS_DROWSINESS"
    )
    assert assignment.id is not None
    assert assignment.status == "ASSIGNED"

    # 5. Tài xế học xong và nộp phản hồi hoàn thành -> Được phục hồi +5.0 điểm an toàn
    completed = await coaching_crud.complete_coaching(
        db=async_db,
        coaching_id=assignment.id,
        company_id=1,
        driver_id=20,
        driver_notes="Đã nắm rõ quy tắc dừng xe nghỉ ngơi 15 phút sau mỗi 2 giờ lái xe",
        bonus_points=5.0
    )
    assert completed.status == "COMPLETED"
    assert completed.score_restored == 5.0

    # Kiểm tra điểm tài xế được phục hồi: 77.0 + 5.0 = 82.0
    refreshed_driver = await async_db.get(Driver, 20)
    assert refreshed_driver.safety_score == 82.0
