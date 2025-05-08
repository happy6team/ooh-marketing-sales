import pandas as pd
from models.db_model import CampaignStatus
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

async def load_campaign_status(file_path: str, db: AsyncSession):
    df = pd.read_csv(file_path)
    
    for _, row in df.iterrows():
        # campaign_status_id가 이미 존재하는지 확인
        result = await db.execute(select(CampaignStatus).filter_by(campaign_status_id=row["campaign_status_id"]))
        existing_status = result.scalar_one_or_none()  # 결과가 있으면 existing_status에 객체를 반환
        
        if existing_status is None:
            # 존재하지 않으면 새로운 데이터 삽입
            db.add(CampaignStatus(
                campaign_status_id=row["campaign_status_id"],
                status_name=row["status_name"]
            ))
    
    await db.commit()
