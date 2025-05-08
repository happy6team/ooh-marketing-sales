# main.py
from fastapi import FastAPI, Depends
from db import AsyncSessionLocal
from loaders.data_loader import load_all_data
from db import init_db, get_db

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

@app.get("/example")
async def example():
    return {"message": "Hello"}

from sqlalchemy.ext.asyncio import AsyncSession
from prototype import CallingState, run, save_to_mariadb_async
@app.get("/process_call_data")
async def process_call_data(session: AsyncSession = Depends(get_db)):
    state = CallingState(
        full_text="",
        summary="",
        messages=[]  # 예시로 빈 리스트로 설정
    )

    # run 함수 실행하여 결과 얻기
    fields = run(state)

    # 비동기적으로 MariaDB에 데이터 저장
    await save_to_mariadb_async(fields, session)

    return {"message": "Call data processed and saved successfully"}