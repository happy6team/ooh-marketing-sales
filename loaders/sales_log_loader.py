import pandas as pd
from models.db_model import SalesLog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

async def load_sales_log(file_path: str, db: AsyncSession):
    df = pd.read_csv(file_path)
    
    for _, row in df.iterrows():
        # sales_log_id가 이미 존재하는지 확인
        result = await db.execute(select(SalesLog).filter_by(sales_log_id=row["sales_log_id"]))
        existing_sales_log = result.scalar_one_or_none()  # 결과가 있으면 existing_sales_log에 객체를 반환
        
        if existing_sales_log is None:
            # 존재하지 않으면 새로운 데이터 삽입
            db.add(SalesLog(
                sales_log_id=row["sales_log_id"],
                brand_id=row["brand_id"],
                brand_name=row["brand_name"],
                manager_name=row["manager_name"],
                manager_email=row["manager_email"],
                agent_name=row["agent_name"],
                contact_time=row["contact_time"],
                contact_method=row["contact_method"],
                call_memo=row["call_memo"],
                client_needs_summary=row["client_needs_summary"],
                followup_date=row["followup_date"],
                sales_status_id=row["sales_status_id"],
                proposal_uri=row["proposal_uri"],
                is_proposal_generated=row["is_proposal_generated"],
                last_updated_at=row["last_updated_at"],
                remarks=row["remarks"]
            ))
    
    await db.commit()
