import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from models.model import Brand

async def load_brand(file_path: str, db: AsyncSession):
    df = pd.read_csv(file_path)

    for _, row in df.iterrows():
        brand = Brand(
            brand_id=row["brand_id"],
            subsidiary_id=row["subsidiary_id"],
            brand_name=row["brand_name"],
            main_phone_number=row["main_phone_number"],
            manager_email=row["manager_email"],
            manager_phone_number=row["manager_phone_number"],
            sales_status_id=row["sales_status_id"],
            sales_status_note=row["sales_status_note"]
        )
        db.add(brand)

    await db.commit()
