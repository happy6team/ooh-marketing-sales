import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models.db_model import SalesLog

async def load_sales_log(file_path: str, db: AsyncSession):
    # 빈 문자열을 NaN으로 변환하지 않도록 na_filter=False 설정
    df = pd.read_csv(file_path, na_filter=False)

    # 문자열 → datetime 변환
    df["contact_time"] = pd.to_datetime(df["contact_time"])
    df["last_updated_at"] = pd.to_datetime(df["last_updated_at"])

    for _, row in df.iterrows():
        result = await db.execute(select(SalesLog).filter_by(sales_log_id=row["sales_log_id"]))
        existing_log = result.scalar_one_or_none()

        if existing_log is None:
            # 빈 문자열이나 'nan' 문자열을 None으로 변환
            proposal_url = row["proposal_url"]
            if proposal_url == '' or proposal_url == 'nan':
                proposal_url = None
            
            log = SalesLog(
                sales_log_id=row["sales_log_id"],
                brand_id=row["brand_id"],
                brand_name=row["brand_name"],
                manager_name=row["manager_name"],
                manager_email=row["manager_email"],
                agent_name=row["agent_name"],
                contact_time=row["contact_time"],
                contact_method=row["contact_method"],
                call_full_text=row["call_full_text"],
                call_memo=row["call_memo"],
                client_needs_summary=row["client_needs_summary"],
                sales_status=row["sales_status"],
                proposal_url=proposal_url,
                is_proposal_generated=bool(int(row["is_proposal_generated"])),  # CSV의 boolean 값을 명시적으로 변환
                last_updated_at=row["last_updated_at"],
                remarks=row["remarks"]
            )
            db.add(log)

    await db.commit()