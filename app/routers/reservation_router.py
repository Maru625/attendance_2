from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
from app.schemas import Reservation
from app.services.camera_service import get_image_path, trigger_camera
from app.services import reservation_service
from apscheduler.schedulers.background import BackgroundScheduler

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


@router.post("/schedule")
async def schedule_reservation(reservation: Reservation):
    
    try:
        target_dt = _parse_datetime(reservation.date, reservation.time)
        target_dt_str = f"{reservation.date} {reservation.time}"
    except ValueError:
        raise HTTPException(status_code=400, detail="잘못된 날짜/시간 형식입니다.")

    now = datetime.now()
    
    # 이미지 확인
    image_path = get_image_path(reservation.name)
    if not image_path:
        return JSONResponse(status_code=404, content={"message": f"'{reservation.name}'에 해당하는 이미지를 'images' 폴더에서 찾을 수 없습니다."})

    # 과거 시간 검증
    if target_dt <= now:
        return JSONResponse(status_code=400, content={"message": "현재 시간 이전의 예약은 등록할 수 없습니다."})

    # 중복 예약 검증: 같은 사람 + 같은 날짜 + 같은 유형은 1건만
    existing = reservation_service.get_all()
    for r in existing:
        if r.get('name') == reservation.name and r.get('date') == reservation.date and r.get('type') == reservation.type:
            return JSONResponse(status_code=400, content={
                "message": f"'{reservation.name}'님은 {reservation.date}에 이미 {reservation.type} 예약이 있습니다."
            })

    # 예약 정보 저장
    res_entry = reservation.dict()
    res_entry['target_dt'] = target_dt_str
    res_entry = reservation_service.add(res_entry)

    # 스케줄링
    scheduler.add_job(trigger_camera, 'date', run_date=target_dt, args=[reservation.name])
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
        return JSONResponse(status_code=400, content={"message": "현재 시간 이전의 예약은 등록할 수 없습니다."})

    image_path = get_image_path(reservation.name)
    if not image_path:
        return JSONResponse(status_code=404, content={"message": f"'{reservation.name}'에 해당하는 이미지를 'images' 폴더에서 찾을 수 없습니다."})

    # 중복 예약 검증 (자기 자신 제외)
    existing = reservation_service.get_all()
    for r in existing:
        if r.get('id') != reservation_id and r.get('name') == reservation.name and r.get('date') == reservation.date and r.get('type') == reservation.type:
            return JSONResponse(status_code=400, content={
                "message": f"'{reservation.name}'님은 {reservation.date}에 이미 {reservation.type} 예약이 있습니다."
            })

    updated_entry = reservation.dict()
    updated_entry['target_dt'] = target_dt_str

    result = reservation_service.update(reservation_id, updated_entry)
    if result is None:
        return JSONResponse(status_code=404, content={"message": "해당 예약을 찾을 수 없습니다."})

    # 새 시간으로 스케줄 재등록
    scheduler.add_job(trigger_camera, 'date', run_date=target_dt, args=[reservation.name])
    
    return {"message": f"{target_dt_str}으로 수정되었습니다.", "reservation": result}


@router.delete("/schedule/{reservation_id}")
async def delete_reservation(reservation_id: str):
    """예약 삭제"""
    success = reservation_service.remove(reservation_id)
    if not success:
        return JSONResponse(status_code=404, content={"message": "해당 예약을 찾을 수 없습니다."})
    return {"message": "예약이 삭제되었습니다."}


@router.get("/reservations")
async def get_reservations():
    """전체 예약 목록"""
    return reservation_service.get_all()


@router.get("/reservations/{type_name}")
async def get_reservations_by_type(type_name: str):
    """유형별 예약 목록 (출근/퇴근)"""
    return reservation_service.get_by_type(type_name)
