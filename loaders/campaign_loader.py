import pandas as pd
from models.db_model import Campaign
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

async def load_campaign(file_path: str, db: AsyncSession):
    df = pd.read_csv(file_path)
    
    for _, row in df.iterrows():
        # campaign_id가 이미 존재하는지 확인
        result = await db.execute(select(Campaign).filter_by(campaign_id=row["campaign_id"]))
        existing_campaign = result.scalar_one_or_none()  # 결과가 있으면 existing_campaign에 객체를 반환
        
        if existing_campaign is None:
            # 존재하지 않으면 새로운 데이터 삽입
            db.add(Campaign(
                campaign_id=row["campaign_id"],
                brand_id=row["brand_id"],
                start_date=row["start_date"],
                end_date=row["end_date"],
                status_id=row["status_id"],
                total_budget=row["total_budget"]
            ))
    
    await db.commit()
