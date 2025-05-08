import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from models.db_model import Brand
from sqlalchemy.future import select
from datetime import datetime

async def load_brand(file_path: str, db: AsyncSession):
    df = pd.read_csv(file_path)

    for _, row in df.iterrows():
        result = await db.execute(
            select(Brand).filter(Brand.brand_id == row["brand_id"])
        )
        existing_brand = result.scalar_one_or_none()

        if existing_brand is None:
            # last_updated_at 변환 처리
            last_updated = None
            if pd.notna(row.get("last_updated_at", None)):
                last_updated = datetime.strptime(row["last_updated_at"], "%Y-%m-%d %H:%M:%S")

            brand = Brand(
                brand_id=row["brand_id"],
                subsidiary_id=row["subsidiary_id"],
                brand_name=row["brand_name"],
                main_phone_number=row["main_phone_number"],
                manager_email=row["manager_email"],
                manager_phone_number=row["manager_phone_number"],
                sales_status=row["sales_status"],
                sales_status_note=row["sales_status_note"],
                category=row["category"],
                core_product_summary=row["core_product_summary"],
                recent_brand_issues=row["recent_brand_issues"],
                last_updated_at=last_updated
            )
            db.add(brand)

    await db.commit()
