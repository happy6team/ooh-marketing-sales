import pandas as pd
from models.model import Media
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

async def load_media(file_path: str, db: AsyncSession):
    df = pd.read_csv(file_path)
    
    for _, row in df.iterrows():
        # media_id가 이미 존재하는지 확인
        result = await db.execute(select(Media).filter_by(media_id=row["media_id"]))
        existing_media = result.scalar_one_or_none()  # 결과가 있으면 existing_media에 객체를 반환
        
        if existing_media is None:
            # 존재하지 않으면 새로운 데이터 삽입
            db.add(Media(
                media_id=row["media_id"],
                media_name=row["media_name"],
                location=row["location"],
                specification=row["specification"],
                slot_count=row["slot_count"],
                media_type=row["media_type"],
                operating_hours=row["operating_hours"],
                guaranteed_exposure=row["guaranteed_exposure"],
                duration_seconds=row["duration_seconds"],
                quantity=row["quantity"],
                unit_price=row["unit_price"],
                features=row["features"],
                image_day_url=row["image_day_url"],
                image_night_url=row["image_night_url"],
                image_map_url=row["image_map_url"]
            ))
    
    await db.commit()
