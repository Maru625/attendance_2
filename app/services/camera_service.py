"""
camera_service.py
- 상시 실행: 물리 카메라 → 가상 카메라 패스스루
- 트리거 시: 지정된 이미지를 가상 카메라로 전송 (30초)
- 트리거 종료 후: 다시 패스스루로 복귀
"""

import os
import time
import threading
import logging
import cv2
import pyvirtualcam
import numpy as np

logger = logging.getLogger(__name__)

# === 상태 관리 ===
_lock = threading.Lock()
_inject_image: np.ndarray | None = None  # 주입할 이미지 (RGB)
_inject_until: float = 0.0               # 주입 종료 시각 (unix timestamp)
_running = False
_thread: threading.Thread | None = None

INJECT_DURATION = 5  # 이미지 주입 시간 (초)


import unicodedata

def get_image_path(name: str) -> str | None:
    """이미지 이름을 기반으로 실제 파일 경로 찾기 (.jpg, .png, .jpeg 대소문자 무관, 유니코드 정규화)"""
    # 현재 파일(camera_service.py) 기준 3단계 위가 프로젝트 루트
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    images_dir = os.path.join(base_dir, "images")
    
    if not os.path.exists(images_dir):
        logger.error(f"이미지 폴더를 찾을 수 없습니다: {images_dir}")
        return None
        
    # 입력된 이름 정규화 (Mac/Window 복사 시 발생하는 자소 분리 문제 해결)
    target_name = unicodedata.normalize('NFC', name).strip()
        
    try:
        for filename in os.listdir(images_dir):
            file_base, file_ext = os.path.splitext(filename)
            # 디렉토리에 있는 파일 이름도 정규화
            normalized_base = unicodedata.normalize('NFC', file_base).strip()
            
            # 파일 이름이 일치하고, 확장자가 이미지인 경우
            if normalized_base == target_name and file_ext.lower() in [".jpg", ".jpeg", ".png"]:
                return os.path.join(images_dir, filename)
    except Exception as e:
        logger.error(f"이미지 폴더 읽기 오류: {e}")
        
    return None


def trigger_camera(name: str):
    """예약된 시간에 호출 — 이미지를 주입 상태로 전환"""
    global _inject_image, _inject_until

    image_path = get_image_path(name)
    if not image_path:
        logger.error(f"이미지를 찾을 수 없습니다: {name}")
        return

    # cv2.imread 대신 numpy와 imdecode를 사용하여 한글 경로 문제 해결
    try:
        img_array = np.fromfile(image_path, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("imdecode returned None")
    except Exception as e:
        logger.error(f"이미지를 로드할 수 없습니다: {image_path} ({e})")
        return

    # BGR → RGB (pyvirtualcam은 RGB)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    with _lock:
        _inject_image = img_rgb
        _inject_until = time.time() + INJECT_DURATION

    logger.info(f"카메라 주입 시작: {name} ({INJECT_DURATION}초간)")


def _camera_loop():
    """백그라운드 스레드: 물리 카메라 → 가상 카메라 중계 루프"""
    global _inject_image, _inject_until, _running

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        logger.error("물리 카메라를 열 수 없습니다.")
        _running = False
        return

    # 카메라 해상도 가져오기
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = 20

    logger.info(f"물리 카메라 열림: {w}x{h}")

    try:
        with pyvirtualcam.Camera(width=w, height=h, fps=fps) as cam:
            logger.info(f"가상 카메라 시작: {cam.device}")

            while _running:
                now = time.time()

                with _lock:
                    injecting = _inject_image is not None and now < _inject_until
                    current_inject = _inject_image if injecting else None

                    # 주입 시간이 지나면 상태 초기화
                    if _inject_image is not None and now >= _inject_until:
                        logger.info("카메라 주입 종료 → 패스스루 복귀")
                        _inject_image = None

                if injecting and current_inject is not None:
                    # === 이미지 주입 모드 ===
                    # 물리 카메라 프레임을 배경으로 사용
                    ret, bg_frame = cap.read()
                    if ret:
                        frame = cv2.cvtColor(bg_frame, cv2.COLOR_BGR2RGB)
                    else:
                        frame = np.zeros((h, w, 3), dtype=np.uint8)

                    # QR 이미지를 카메라 중앙, 세로 50% 크기의 정사각형에 맞춤
                    box_size = int(h * 0.5)
                    qr_resized = cv2.resize(current_inject, (box_size, box_size))

                    # 중앙 위치 계산
                    x1 = (w - box_size) // 2
                    y1 = (h - box_size) // 2
                    x2 = x1 + box_size
                    y2 = y1 + box_size

                    # 배경 위에 QR 이미지 합성
                    frame[y1:y2, x1:x2] = qr_resized

                    cam.send(frame)
                else:
                    # === 패스스루 모드 ===
                    ret, raw_frame = cap.read()
                    if not ret:
                        continue
                    # BGR → RGB
                    frame = cv2.cvtColor(raw_frame, cv2.COLOR_BGR2RGB)
                    cam.send(frame)

                cam.sleep_until_next_frame()

    except Exception as e:
        logger.error(f"카메라 루프 에러: {e}")
    finally:
        cap.release()
        _running = False
        logger.info("카메라 루프 종료")


def start():
    """카메라 패스스루 서비스 시작 (백그라운드 스레드)"""
    global _running, _thread

    if _running:
        logger.warning("카메라 서비스가 이미 실행 중입니다.")
        return

    _running = True
    _thread = threading.Thread(target=_camera_loop, daemon=True)
    _thread.start()
    logger.info("카메라 패스스루 서비스 시작됨")


def stop():
    """카메라 패스스루 서비스 종료"""
    global _running
    _running = False
    if _thread:
        _thread.join(timeout=5)
    logger.info("카메라 패스스루 서비스 종료됨")


def is_running() -> bool:
    return _running
