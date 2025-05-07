# 비동기 DB 연결 설정

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from models.model import Base

# MariaDB 안에 ooh_db 스키마가 있어야 함(실행 전 만들어 놓기)
ASYNC_DB_URL = "mysql+aiomysql://ooh_manager:oohmanager0507@127.0.0.1:3306/ooh_db?charset=utf8mb4"

async_engine = create_async_engine(ASYNC_DB_URL, echo=True)

AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def init_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
