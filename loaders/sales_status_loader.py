import pandas as pd
from models.model import SalesStatus
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

async def load_sales_status(file_path: str, db: AsyncSession):
    df = pd.read_csv(file_path)
    
    for _, row in df.iterrows():
        # sales_status_id가 이미 존재하는지 확인
        result = await db.execute(select(SalesStatus).filter_by(sales_status_id=row["sales_status_id"]))
        existing_sales_status = result.scalar_one_or_none()  # 결과가 있으면 existing_sales_status에 객체를 반환
        
        if existing_sales_status is None:
            # 존재하지 않으면 새로운 데이터 삽입
            db.add(SalesStatus(
                sales_status_id=row["sales_status_id"],
                status_name=row["status_name"],
                description=row["description"],
                sort_order=row["sort_order"],
                is_final=row["is_final"]
            ))
    
    await db.commit()
