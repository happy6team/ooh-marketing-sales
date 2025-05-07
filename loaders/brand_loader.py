import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from models.model import Brand
from sqlalchemy.future import select

async def load_brand(file_path: str, db: AsyncSession):
    df = pd.read_csv(file_path)

    for _, row in df.iterrows():
        # brand_id가 이미 존재하는지 확인
        result = await db.execute(select(Brand).filter_by(brand_id=row["brand_id"]))
        existing_brand = result.scalar_one_or_none()  # 결과가 있으면 existing_brand에 객체를 반환
        
        if existing_brand is None:
            # 존재하지 않으면 새로운 데이터 삽입
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
