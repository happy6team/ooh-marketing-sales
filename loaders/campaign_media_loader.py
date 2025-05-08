import pandas as pd
from models.db_model import CampaignMedia
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime

async def load_campaign_media(file_path: str, db: AsyncSession):
    df = pd.read_csv(file_path)
    
    for _, row in df.iterrows():
        # campaign_media_id가 이미 존재하는지 확인
        result = await db.execute(select(CampaignMedia).filter(CampaignMedia.campaign_media_id == row["campaign_media_id"]))
        existing_media = result.scalar_one_or_none()  # 결과가 있으면 existing_media에 객체를 반환
        
        if existing_media is None:
            # 존재하지 않으면 새로운 데이터 삽입
            campaign_media = CampaignMedia(
                campaign_media_id=row["campaign_media_id"],
                campaign_id=row["campaign_id"],
                media_id=row["media_id"],
                # 날짜를 datetime으로 변환
                start_date=datetime.strptime(row["start_date"], "%Y-%m-%d") if pd.notna(row["start_date"]) else None,
                end_date=datetime.strptime(row["end_date"], "%Y-%m-%d") if pd.notna(row["end_date"]) else None,
                slot_count=row["slot_count"],
                executed_price=row["executed_price"],
                execution_image_url=row["execution_image_url"],
                campaign_media_status=row["campaign_media_status"]  # 수정된 필드명
            )
            db.add(campaign_media)
    
    await db.commit()
