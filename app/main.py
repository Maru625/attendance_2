import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from app.routers import reservation_router
from app.services import camera_service

# 로깅 설정
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작 시 카메라 서비스 시작, 종료 시 정리"""
    camera_service.start()
    yield
    camera_service.stop()


app = FastAPI(lifespan=lifespan)

# 정적 파일 서빙
app.mount("/static", StaticFiles(directory="static"), name="static")

# 라우터 등록
app.include_router(reservation_router.router)


@app.get("/")
async def serve_spa():
    return JSONResponse(content={"message": "Please go to /static/index.html"})
