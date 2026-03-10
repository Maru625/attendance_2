import os
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from apscheduler.schedulers.background import BackgroundScheduler
import pyvirtualcam
import cv2
import numpy as np

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# 정적 파일 서빙
app.mount("/static", StaticFiles(directory="static"), name="static")

# 예약 저장을 위한 인메모리 저장소
reservations = []

# 스케줄러 설정
scheduler = BackgroundScheduler()
scheduler.start()

class Reservation(BaseModel):
    name: str
    date: str
    time: str
    type: str

def get_image_path(name: str):
    # 이미지 확장자 지원 (.jpg, .png, .jpeg)
    base_path = os.path.join("images", name)
    for ext in [".jpg", ".png", ".jpeg"]:
        if os.path.exists(base_path + ext):
            return base_path + ext
    return None

def trigger_camera(name: str):
    logger.info(f"Starting camera interception for {name}")
    image_path = get_image_path(name)
    
    if not image_path:
        logger.error(f"Image not found for {name}")
        return

    try:
        # 이미지 로드
        img = cv2.imread(image_path)
        if img is None:
            logger.error(f"Failed to load image: {image_path}")
            return
            
        # OpenCV는 BGR, pyvirtualcam은 RGB를 기대함
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, _ = img.shape

        # 가상 카메라로 전송
        # fmt=pyvirtualcam.PixelFormat.RGB 가 기본값
        with pyvirtualcam.Camera(width=w, height=h, fps=20) as cam:
            logger.info(f"Virtual Camera started: {cam.device}")
            # 30초 동안 이미지 송출
            start_time = time.time()
            while time.time() - start_time < 30:
                cam.send(img)
                cam.sleep_until_next_frame()
                
        logger.info(f"Camera interception finished for {name}")
        
    except Exception as e:
        logger.error(f"Error during camera interception: {e}")
        # 가상 카메라가 없는 경우 등에 대한 에러 처리
        if "No virtual camera found" in str(e):
            logger.error("OBS Virtual Camera가 설치되어 있고 켜져 있는지 확인해주세요.")

    # 작업 완료 후 예약 목록에서 제거 (선택 사항, 로직에 따라 다름)
    # 여기서는 스케줄러가 일회성이므로 자동 종료됨, 리스트에서는 별도 제거 로직 필요시 추가

@app.post("/schedule")
async def schedule_reservation(reservation: Reservation):
    global reservations
    
    # 시간 파싱
    try:
        target_dt_str = f"{reservation.date} {reservation.time}"
        target_dt = datetime.strptime(target_dt_str, "%Y-%m-%d %H:%M")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date/time format")

    now = datetime.now()
    
    # 예약 정보 저장
    res_entry = reservation.dict()
    res_entry['id'] = str(len(reservations) + 1) # 간단한 ID
    res_entry['target_dt'] = target_dt_str
    
    
    image_path = get_image_path(reservation.name)
    if not image_path:
        return JSONResponse(status_code=404, content={"message": f"'{reservation.name}'에 해당하는 이미지를 'images' 폴더에서 찾을 수 없습니다."})

    reservations.append(res_entry)

    # 스케줄링
    if target_dt <= now:
        # 이미 지났거나 현재면 즉시 실행 (백그라운드 태스크로)
        scheduler.add_job(trigger_camera, 'date', run_date=datetime.now() + timedelta(seconds=1), args=[reservation.name])
        message = "시간이 도달하여 즉시 실행됩니다."
    else:
        # 미래 시간이면 예약
        scheduler.add_job(trigger_camera, 'date', run_date=target_dt, args=[reservation.name])
        message = f"{target_dt_str}에 예약되었습니다."

    return {"message": message, "reservation": res_entry}

@app.get("/reservations")
async def get_reservations():
    # 현재 시간 이후의 예약만 필터링해서 보여주거나 전체 보여주기
    # 완료된 예약 제거 로직
    # 간단하게 전체 리스트 반환
    return reservations

@app.get("/")
async def serve_spa():
    return JSONResponse(content={"message": "Please go to /static/index.html"})
