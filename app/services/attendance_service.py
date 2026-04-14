"""
attendance_service.py
- Selenium 기반 출석 자동화 서비스
- headless Chrome으로 출석 웹사이트 접속 → JS Injection으로 QR 데이터 전송
- 지각 사유 모달 감지 및 자동 제출
"""

import os
import json
import time
import logging
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

logger = logging.getLogger(__name__)

# === 설정 ===
TARGET_URL = "https://construction-montgomery-roof-tagged.trycloudflare.com/attendance"

# 지각 사유 선택지
LATE_REASONS = [
    "교통 지연",
    "개인 사유",
    "업무 관련",
    "기타",
]
DEFAULT_LATE_REASON = "개인 사유"

# === 직원 데이터 ===
_employees: dict[str, str] = {}


def _get_employees_path() -> str:
    """employees.json 파일 경로 반환"""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_dir, "employees.json")


def load_employees() -> dict[str, str]:
    """employees.json에서 직원 목록 로드"""
    global _employees
    path = _get_employees_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            _employees = json.load(f)
        logger.info(f"직원 {len(_employees)}명 로드됨")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"employees.json 로드 실패: {e}")
        _employees = {}
    return _employees


def get_employees() -> dict[str, str]:
    """직원 이름 → QR 데이터 매핑 반환"""
    if not _employees:
        load_employees()
    return _employees


def get_employee_names() -> list[str]:
    """직원 이름 목록 반환"""
    return list(get_employees().keys())


def get_qr_data(name: str) -> str | None:
    """이름으로 QR 고유값 조회"""
    return get_employees().get(name)


def get_late_reasons() -> list[str]:
    """지각 사유 선택지 반환"""
    return LATE_REASONS


def get_default_late_reason() -> str:
    """지각 사유 미입력 시 사용할 기본 사유 반환"""
    return DEFAULT_LATE_REASON


def get_target_url() -> str:
    """현재 설정된 출석 사이트 URL 반환"""
    return TARGET_URL


def set_target_url(url: str):
    """출석 사이트 URL 변경"""
    global TARGET_URL
    TARGET_URL = url
    logger.info(f"출석 사이트 URL 변경: {url}")


# === 사이트 상태 확인 ===
def check_site_health() -> dict:
    """출석 사이트 접속 가능 여부 확인"""
    try:
        resp = requests.get(TARGET_URL, timeout=10)
        if resp.status_code == 200:
            return {"healthy": True, "status_code": resp.status_code, "message": "사이트 정상"}
        else:
            return {"healthy": False, "status_code": resp.status_code, "message": f"HTTP {resp.status_code}"}
    except requests.ConnectionError:
        return {"healthy": False, "status_code": None, "message": "사이트에 연결할 수 없습니다."}
    except requests.Timeout:
        return {"healthy": False, "status_code": None, "message": "사이트 응답 시간 초과 (10초)"}
    except Exception as e:
        return {"healthy": False, "status_code": None, "message": f"알 수 없는 오류: {e}"}


# === 핵심 출석 로직 ===
def _create_driver() -> webdriver.Chrome:
    """headless Chrome WebDriver 생성"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1280,720")
    return webdriver.Chrome(options=chrome_options)


def auto_check_in(qr_data: str, late_reason: str = "") -> dict:
    """
    Selenium으로 출석 처리.
    
    Returns:
        dict with keys:
        - status: "성공" | "실패"
        - message: 상세 메시지
        - timestamp: 처리 시각
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    resolved_late_reason = late_reason.strip() or DEFAULT_LATE_REASON
    
    # 사이트 접속 가능 여부 사전 확인
    health = check_site_health()
    if not health["healthy"]:
        logger.error(f"출석 사이트 접속 불가: {health['message']}")
        return {
            "status": "실패",
            "message": f"출석 사이트 접속 불가: {health['message']}",
            "timestamp": timestamp,
        }
    
    driver = None
    try:
        driver = _create_driver()
        logger.info(f"[{timestamp}] 출석 페이지 접속 중... ({TARGET_URL})")
        driver.get(TARGET_URL)
        
        # 시스템 로딩 대기 (kadaSubmitAttendance 함수가 준비될 때까지)
        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script("return typeof window.kadaSubmitAttendance === 'function'")
        )
        logger.info("출석 시스템 로딩 완료")
        
        # JS Injection으로 출석 데이터 전송
        logger.info(f"QR 데이터({qr_data}) 전송 중...")
        driver.execute_script(f"window.kadaSubmitAttendance('{qr_data}');")
        time.sleep(3)  # 서버 응답 대기
        
        # 지각 사유 모달 확인
        is_modal_open = driver.execute_script(
            "return typeof window.kadaIsAttendanceReasonModalOpen === 'function' "
            "&& window.kadaIsAttendanceReasonModalOpen();"
        )
        
        if is_modal_open:
            logger.info("지각 사유 입력창 감지됨")
            logger.info(f"지각 사유 자동 제출: {resolved_late_reason}")
            driver.execute_script(
                f"window.kadaSubmitAttendanceReason('{resolved_late_reason}');"
            )
            time.sleep(2)
            return {
                "status": "성공",
                "message": f"지각 처리 완료 (사유: {resolved_late_reason})",
                "timestamp": timestamp,
            }
        
        # 정상 출석 완료
        logger.info("출석 완료")
        return {
            "status": "성공",
            "message": "출석이 정상 처리되었습니다.",
            "timestamp": timestamp,
        }
        
    except Exception as e:
        logger.error(f"출석 중 오류 발생: {e}")
        return {
            "status": "실패",
            "message": f"출석 처리 중 오류: {str(e)}",
            "timestamp": timestamp,
        }
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass


def submit_late_reason(qr_data: str, late_reason: str) -> dict:
    """
    지각 사유를 별도로 제출 (사유입력필요 상태에서 호출).
    출석 사이트에 다시 접속하여 QR 전송 후 사유 모달에 입력.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    driver = None
    try:
        driver = _create_driver()
        driver.get(TARGET_URL)
        
        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script("return typeof window.kadaSubmitAttendance === 'function'")
        )
        
        # QR 재전송 → 모달 재표시
        driver.execute_script(f"window.kadaSubmitAttendance('{qr_data}');")
        time.sleep(3)
        
        is_modal_open = driver.execute_script(
            "return typeof window.kadaIsAttendanceReasonModalOpen === 'function' "
            "&& window.kadaIsAttendanceReasonModalOpen();"
        )
        
        if is_modal_open:
            driver.execute_script(f"window.kadaSubmitAttendanceReason('{late_reason}');")
            time.sleep(2)
            return {
                "status": "성공",
                "message": f"지각 사유 제출 완료: {late_reason}",
                "timestamp": timestamp,
            }
        else:
            # 모달이 안 뜨면 이미 처리된 것
            return {
                "status": "성공",
                "message": "이미 출석이 처리되었습니다.",
                "timestamp": timestamp,
            }
    
    except Exception as e:
        logger.error(f"지각 사유 제출 오류: {e}")
        return {
            "status": "실패",
            "message": f"사유 제출 중 오류: {str(e)}",
            "timestamp": timestamp,
        }
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
