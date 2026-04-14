from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
from app.schemas import Reservation
from app.services import attendance_service, reservation_service
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# 스케줄러
scheduler = BackgroundScheduler()
scheduler.start()


def _parse_datetime(date: str, time: str) -> datetime:
    """날짜와 시간 문자열을 datetime으로 변환"""
    dt_str = f"{date} {time}"
    if len(time.split(":")) == 3:
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    else:
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M")


def _execute_check_in(reservation_id: str, name: str, late_reason: str = ""):
    """스케줄러에서 호출되는 출석 실행 함수"""
    qr_data = attendance_service.get_qr_data(name)
    if not qr_data:
        reservation_service.update_status(reservation_id, "실패", f"'{name}' QR 데이터 없음")
        return

    # 상태: 진행중
    reservation_service.update_status(reservation_id, "진행중")

    # 출석 실행
    result = attendance_service.auto_check_in(qr_data, late_reason)

    # 결과 저장
    reservation_service.update_status(
        reservation_id, result["status"], result["message"]
    )
    logger.info(f"출석 결과 [{name}]: {result['status']} - {result['message']}")


def load_saved_jobs():
    """서버 시작 시 미래의 예약들을 스케줄러에 등록"""
    reservations = reservation_service.get_all()
    now = datetime.now()
    count = 0
    for r in reservations:
        try:
            target_dt = _parse_datetime(r['date'], r['time'])
            if target_dt > now and r.get('status', '대기중') == '대기중':
                scheduler.add_job(
                    _execute_check_in, 'date',
                    run_date=target_dt,
                    args=[r['id'], r['name'], r.get('late_reason', '')],
                    id=r['id'],
                    replace_existing=True,
                )
                count += 1
        except Exception as e:
            logger.error(f"예약 스케줄 복원 오류: {e}")
    logger.info(f"총 {count}개의 미래 예약을 스케줄러에 등록했습니다.")


def cleanup_old_reservations():
    """7일이 지난 과거 예약 자동 삭제 (매일 자정 실행)"""
    reservations = reservation_service.get_all()
    cutoff_dt = datetime.now() - timedelta(days=7)
    count = 0

    for r in reservations:
        try:
            target_dt = _parse_datetime(r['date'], r['time'])
            if target_dt < cutoff_dt:
                reservation_service.remove(r['id'])
                count += 1
        except Exception as e:
            logger.error(f"예약 자동 청소 오류: {e}")

    if count > 0:
        logger.info(f"7일이 지난 과거 예약 {count}건을 자동 삭제했습니다.")


# 매일 자정(00:00)에 과거 예약 청소 스케줄 등록
scheduler.add_job(
    cleanup_old_reservations, 'cron',
    hour=0, minute=0,
    id='cleanup_7days_job',
    replace_existing=True,
)

# 서버 시동 시 기존 예약 복원
load_saved_jobs()


# ==========================================
# API 엔드포인트
# ==========================================

@router.get("/employees")
async def get_employees():
    """등록된 직원 이름 목록 반환"""
    return attendance_service.get_employee_names()


@router.get("/late-reasons")
async def get_late_reasons():
    """지각 사유 선택지 반환"""
    return attendance_service.get_late_reasons()


@router.get("/site-health")
async def get_site_health():
    """출석 사이트 접속 상태 확인"""
    return attendance_service.check_site_health()


@router.post("/schedule")
async def schedule_reservation(reservation: Reservation):

    try:
        target_dt = _parse_datetime(reservation.date, reservation.time)
        target_dt_str = f"{reservation.date} {reservation.time}"
    except ValueError:
        raise HTTPException(status_code=400, detail="잘못된 날짜/시간 형식입니다.")

    now = datetime.now()

    # 직원 등록 여부 확인
    qr_data = attendance_service.get_qr_data(reservation.name)
    if not qr_data:
        return JSONResponse(
            status_code=404,
            content={"message": f"'{reservation.name}'은(는) 등록된 직원이 아닙니다."},
        )

    # 과거 시간 검증
    if target_dt <= now:
        return JSONResponse(
            status_code=400,
            content={"message": "현재 시간 이전의 예약은 등록할 수 없습니다."},
        )

    # 중복 예약 검증: 같은 사람 + 같은 날짜 + 같은 유형은 1건만
    existing = reservation_service.get_all()
    for r in existing:
        if (
            r.get('name') == reservation.name
            and r.get('date') == reservation.date
            and r.get('type') == reservation.type
        ):
            return JSONResponse(
                status_code=400,
                content={
                    "message": f"'{reservation.name}'님은 {reservation.date}에 이미 {reservation.type} 예약이 있습니다."
                },
            )

    # 예약 정보 저장
    res_entry = reservation.dict()
    res_entry['target_dt'] = target_dt_str
    res_entry['status'] = '대기중'
    res_entry = reservation_service.add(res_entry)

    # 스케줄링
    scheduler.add_job(
        _execute_check_in, 'date',
        run_date=target_dt,
        args=[res_entry['id'], reservation.name, reservation.late_reason or ''],
        id=res_entry['id'],
        replace_existing=True,
    )
    message = f"{target_dt_str}에 예약되었습니다."

    return {"message": message, "reservation": res_entry}


@router.put("/schedule/{reservation_id}")
async def update_reservation(reservation_id: str, reservation: Reservation):
    """예약 수정"""
    try:
        target_dt = _parse_datetime(reservation.date, reservation.time)
        target_dt_str = f"{reservation.date} {reservation.time}"
    except ValueError:
        raise HTTPException(status_code=400, detail="잘못된 날짜/시간 형식입니다.")

    now = datetime.now()
    if target_dt <= now:
        return JSONResponse(
            status_code=400,
            content={"message": "현재 시간 이전의 예약은 등록할 수 없습니다."},
        )

    qr_data = attendance_service.get_qr_data(reservation.name)
    if not qr_data:
        return JSONResponse(
            status_code=404,
            content={"message": f"'{reservation.name}'은(는) 등록된 직원이 아닙니다."},
        )

    # 중복 예약 검증 (자기 자신 제외)
    existing = reservation_service.get_all()
    for r in existing:
        if (
            r.get('id') != reservation_id
            and r.get('name') == reservation.name
            and r.get('date') == reservation.date
            and r.get('type') == reservation.type
        ):
            return JSONResponse(
                status_code=400,
                content={
                    "message": f"'{reservation.name}'님은 {reservation.date}에 이미 {reservation.type} 예약이 있습니다."
                },
            )

    updated_entry = reservation.dict()
    updated_entry['target_dt'] = target_dt_str
    updated_entry['status'] = '대기중'

    result = reservation_service.update(reservation_id, updated_entry)
    if result is None:
        return JSONResponse(
            status_code=404,
            content={"message": "해당 예약을 찾을 수 없습니다."},
        )

    # 새 시간으로 스케줄 덮어쓰기
    scheduler.add_job(
        _execute_check_in, 'date',
        run_date=target_dt,
        args=[reservation_id, reservation.name, reservation.late_reason or ''],
        id=reservation_id,
        replace_existing=True,
    )

    return {"message": f"{target_dt_str}으로 수정되었습니다.", "reservation": result}


@router.delete("/schedule/{reservation_id}")
async def delete_reservation(reservation_id: str):
    """예약 삭제"""
    success = reservation_service.remove(reservation_id)
    if not success:
        return JSONResponse(
            status_code=404,
            content={"message": "해당 예약을 찾을 수 없습니다."},
        )

    # 스케줄러에서 작업 취소
    try:
        scheduler.remove_job(reservation_id)
    except JobLookupError:
        pass  # 이미 실행되었거나 없는 작업은 무시

    return {"message": "예약이 삭제되었습니다."}


@router.get("/reservations")
async def get_reservations():
    """전체 예약 목록"""
    return reservation_service.get_all()


@router.get("/reservations/{type_name}")
async def get_reservations_by_type(type_name: str):
    """유형별 예약 목록 (출근/퇴근)"""
    return reservation_service.get_by_type(type_name)
