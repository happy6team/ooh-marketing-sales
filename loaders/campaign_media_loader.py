import pandas as pd
from models.model import CampaignMedia
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

async def load_campaign_media(file_path: str, db: AsyncSession):
    df = pd.read_csv(file_path)
    
    for _, row in df.iterrows():
        # campaign_media_id가 이미 존재하는지 확인
        result = await db.execute(select(CampaignMedia).filter_by(campaign_media_id=row["campaign_media_id"]))
        existing_media = result.scalar_one_or_none()  # 결과가 있으면 existing_media에 객체를 반환
        
        if existing_media is None:
            # 존재하지 않으면 새로운 데이터 삽입
            db.add(CampaignMedia(
                campaign_media_id=row["campaign_media_id"],
                campaign_id=row["campaign_id"],
                media_id=row["media_id"],
                start_date=row["start_date"],
                end_date=row["end_date"],
                slot_count=row["slot_count"],
                executed_price=row["executed_price"],
                execution_image_url=row["execution_image_url"],
                campaign_status_id=row["campaign_status_id"]
            ))
    
    await db.commit()
