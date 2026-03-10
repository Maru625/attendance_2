"""
reservation_service.py
- 예약 정보를 JSON 파일로 영속화
- 서버 재시작 시에도 예약 데이터 유지
"""

import json
import os
import uuid
import threading
import logging

logger = logging.getLogger(__name__)

DATA_FILE = "reservations.json"
_lock = threading.Lock()


def _load() -> list[dict]:
    """JSON 파일에서 예약 목록 로드"""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        logger.error("예약 파일 로드 실패")
        return []


def _save(data: list[dict]):
    """예약 목록을 JSON 파일로 저장"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_all() -> list[dict]:
    """전체 예약 목록 반환"""
    with _lock:
        return _load()


def add(entry: dict) -> dict:
    """예약 추가"""
    with _lock:
        data = _load()
        entry['id'] = str(uuid.uuid4())[:8]
        data.append(entry)
        _save(data)
    return entry


def update(reservation_id: str, updated: dict) -> dict | None:
    """예약 수정"""
    with _lock:
        data = _load()
        for i, r in enumerate(data):
            if r.get('id') == reservation_id:
                updated['id'] = reservation_id
                data[i] = updated
                _save(data)
                return updated
    return None


def remove(reservation_id: str) -> bool:
    """예약 제거"""
    with _lock:
        data = _load()
        new_data = [r for r in data if r.get('id') != reservation_id]
        if len(new_data) == len(data):
            return False
        _save(new_data)
    return True


def get_by_type(type_name: str) -> list[dict]:
    """유형별 예약 목록 반환 (출근/퇴근)"""
    with _lock:
        data = _load()
        return [r for r in data if r.get('type') == type_name]
