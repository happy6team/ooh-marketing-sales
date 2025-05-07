# main.py
from fastapi import FastAPI
from db import AsyncSessionLocal
from loaders.data_loader import load_all_data
from db import init_db

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    try:
        await init_db()
        async with AsyncSessionLocal() as session:
            await load_all_data(session)
    except Exception as e:
        import logging
        logging.exception("Startup data loading failed")
        raise e
