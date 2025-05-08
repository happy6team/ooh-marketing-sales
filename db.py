from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from models.db_model import Base

ASYNC_DB_URL = "mysql+aiomysql://ooh_manager:oohmanager0507@127.0.0.1:3306/oohmarketing?charset=utf8mb4"

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
