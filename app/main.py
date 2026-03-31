import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.routers import reservation_router
from app.services import camera_service

# 로깅 설정
logging.basicConfig(level=logging.INFO)


class NoCacheMiddleware(BaseHTTPMiddleware):
    """모든 응답에 캐시 비활성화 헤더를 추가하여
    ngrok/모바일 브라우저의 캐시 문제를 방지"""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작 시 카메라 서비스 시작, 종료 시 정리"""
    camera_service.start()
    yield
    camera_service.stop()


app = FastAPI(lifespan=lifespan)

# 캐시 비활성화 미들웨어 추가
app.add_middleware(NoCacheMiddleware)

# 정적 파일 서빙
app.mount("/static", StaticFiles(directory="static"), name="static")

# 라우터 등록
app.include_router(reservation_router.router)


@app.get("/")
async def serve_spa():
    return JSONResponse(content={"message": "Please go to /static/index.html"})
