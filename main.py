# main.py
from fastapi import FastAPI
from db import AsyncSessionLocal
from loaders.data_loader import load_all_data
from db import init_db

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    try:
        await init_db() # 테이블 생성
        async with AsyncSessionLocal() as session:
            await load_all_data(session) # 데이터 로드
    except Exception as e:
        import logging
        logging.exception("Startup data loading failed")
        raise e
