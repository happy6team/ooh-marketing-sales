import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.db_model import Media

async def load_media(file_path: str, db: AsyncSession):
    df = pd.read_csv(file_path)
    
    for _, row in df.iterrows():
        # media_id 존재 여부 확인
        result = await db.execute(select(Media).filter_by(media_id=row["media_id"]))
        existing = result.scalar_one_or_none()

        if existing is None:
            media = Media(
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
                image_day_url=row["image_day_url"],
                image_night_url=row["image_night_url"],
                image_map_url=row["image_map_url"],
                population_target=row["population_target"],
                media_characteristics=row["media_characteristics"],
                case_examples=row["case_examples"],
            )
            db.add(media)

    await db.commit()
