import pandas as pd
from models.db_model import Campaign
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime

async def load_campaign(file_path: str, db: AsyncSession):
    df = pd.read_csv(file_path)
    
    for _, row in df.iterrows():
        result = await db.execute(select(Campaign).filter(Campaign.campaign_id == row["campaign_id"]))
        existing_campaign = result.scalar_one_or_none()

        if existing_campaign is None:
            campaign = Campaign(
                campaign_id=row["campaign_id"],
                brand_id=row["brand_id"],
                start_date=datetime.strptime(row["start_date"], "%Y-%m-%d") if pd.notna(row["start_date"]) else None,
                end_date=datetime.strptime(row["end_date"], "%Y-%m-%d") if pd.notna(row["end_date"]) else None,
                campaign_status=row["campaign_status"],  # 문자열 그대로 저장
                total_budget=row["total_budget"]
            )
            db.add(campaign)

    await db.commit()
