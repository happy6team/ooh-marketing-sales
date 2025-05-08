import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from models.db_model import BrandMediaMatch

async def load_brand_media_match(file_path: str, db: AsyncSession):
    df = pd.read_csv(file_path)

    # 데이터베이스에 추가할 데이터 목록 생성
    to_add = []

    for _, row in df.iterrows():
        # 복합 키 (brand_id, media_id)로 존재 여부 확인
        result = await db.execute(
            select(BrandMediaMatch).filter(
                BrandMediaMatch.brand_id == row["brand_id"],
                BrandMediaMatch.media_id == row["media_id"]
            )
        )
        existing = result.scalar_one_or_none()

        if existing is None:
            generated_at = datetime.strptime(row["generated_at"], "%Y-%m-%d %H:%M:%S")
            updated_at = datetime.strptime(row["last_updated_at"], "%Y-%m-%d %H:%M:%S")
            
            proposal_email_parts = row["proposal_email"]
            proposal_email_part_1 = proposal_email_parts[0:65535]
            proposal_email_part_2 = proposal_email_parts[65536:131071]
            proposal_email_part_3 = proposal_email_parts[131072:196607]

            # 데이터 모델 객체를 생성하여 to_add 리스트에 추가
            match = BrandMediaMatch(
                id=row["id"],
                brand_id=row["brand_id"],
                media_id=row["media_id"],
                match_reason=row["match_reason"],
                sales_call_script=row["sales_call_script"],
                proposal_email_part_1=proposal_email_part_1,
                proposal_email_part_2=proposal_email_part_2,
                proposal_email_part_3=proposal_email_part_3,
                generated_at=generated_at,
                used_in_sales=bool(row["used_in_sales"]),
                last_updated_at=updated_at
            )
            to_add.append(match)

    # 한번에 DB에 추가
    if to_add:
        db.add_all(to_add)
        await db.commit()
