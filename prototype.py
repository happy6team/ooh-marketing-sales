from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from faster_whisper import WhisperModel
from typing_extensions import TypedDict, Annotated
from langchain_core.messages import BaseMessage
import openai
import os
from dotenv import load_dotenv
import re
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, func
from models.db_model import SalesLog

from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from models.db_model import Brand
from datetime import datetime
import uuid

# 1️⃣ FastAPI 앱 및 DB 세팅
load_dotenv()

# 3️⃣ State 정의
class CallingState(TypedDict):
    full_text: Annotated[str, "Transcribed Text"]
    summary: Annotated[str, "Summarized Info"]
    messages: Annotated[list[BaseMessage], "Messages"]

# 4️⃣ 빈값 -> None 변환 함수
def empty_to_none(value):
    if value and value.lower() != "nan":
        return value.strip()
    else:
        return None

# 5️⃣ 음성 인식 → State 반환
def transcribe(state: CallingState) -> CallingState:
    model = WhisperModel("base")
    segments, info = model.transcribe("./sil/calling_data.m4a")
    full_text = " ".join([seg.text for seg in segments])
    print("📝 인식된 텍스트:")
    print(full_text)

    return CallingState(
        full_text=full_text,
        summary="",
        messages=[]
    )

# 6️⃣ 요약 및 요구사항 정리 → State 갱신
def summarize(state: CallingState) -> CallingState:
    load_dotenv()
    client = openai.OpenAI()

    prompt = f"""
    다음 고객과의 통화 내용을 요약하고, 고객의 요구사항을 다음 필드별로 정리해줘:
    - 브랜드 이름:
    - 브랜드 담당자 이름:
    - 브랜드 담당자 이메일:
    - 영업 담당자 이름:
    - 영업 접촉 시점:
    - 영업 접촉 방법: 
    - 요구사항 요약:
    - 영업 상태:
    - 비고:
    - 통화 메모:
    - 통화 1줄 요약:
    - 지역:
    - 매체:
    - 타겟층:

    통화 내용:
    \"\"\"{state['full_text']}\"\"\"  
    """

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "너는 영업 담당자의 어시스턴트야. 고객의 요구사항을 정확하게 정리해야 해."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    summary = response.choices[0].message.content
    print("🔎 요약 및 요구사항 정리:")
    print(summary)

    return CallingState(
        full_text=state["full_text"],
        summary=summary,
        messages=[]
    )

def extract_fields(summary: str, full_text: str):
    # 필드별 값 추출 함수
    def extract(label):
        match = re.search(f"{label}: *(.*)", summary)
        return match.group(1).strip() if match else None

    # 필드 추출
    brand_name = extract("브랜드 이름")
    manager_name = extract("브랜드 담당자 이름")
    if not manager_name:
        manager_name = "기본 담당자 이름"  # 기본값 처리
    
    manager_email = extract("브랜드 담당자 이메일")
    if not manager_email:
        manager_email = "default@example.com"  # 기본 이메일 처리
    
    agent_name = extract("영업 담당자 이름")
    contact_method = extract("영업 접촉 방법")
    sales_status = extract("영업 상태")
    sales_status_note = extract("비고")
    
    # call_memo는 GPT의 전체 요약을 그대로 사용
    call_memo = extract("통화 1줄 요약")

    # 고객 요구 요약 (지역, 매체, 타겟층)
    region = extract("지역")
    media = extract("매체")
    target = extract("타겟층")

    summary_parts = []
    if region:
        summary_parts.append(f"{region}")
    if media:
        summary_parts.append(f"{media}")
    if target:
        summary_parts.append(f"{target}")
    client_needs_summary = ", ".join(summary_parts) if summary_parts else None

    # 반환되는 값
    return {
        "brand_name": brand_name,
        "manager_name": manager_name,
        "manager_email": manager_email,
        "agent_name": agent_name,
        "contact_time": datetime.now(),
        "contact_method": contact_method,
        "call_full_text": full_text,
        "call_memo": call_memo,
        "sales_status": sales_status or "미정",  # 기본값 처리
        "proposal_url": None,  # 생성 전이므로 없음
        "is_proposal_generated": False,
        "last_updated_at": datetime.now(),
        "remarks": sales_status_note,  # 비고 필드로 연결
        "client_needs_summary":client_needs_summary
    }

# brand 있으면 조회해서 아이디 가져오고 없으면 brand 새로 생성
async def get_or_create_brand(session: AsyncSession, brand_data: dict) -> int | None:
    try:
        # 브랜드명 기준 조회
        stmt = select(Brand).where(Brand.brand_name == brand_data["brand_name"].strip())
        result = await session.execute(stmt)
        brand = result.scalars().first()

        if brand:
            return brand.brand_id  # 이미 존재하는 경우 해당 ID 반환

        # 마지막 브랜드 ID 조회
        last_id_query = select(func.max(Brand.brand_id))
        last_id_result = await session.execute(last_id_query)
        last_id = last_id_result.scalar() or 0  # None인 경우 0으로 설정
        
        new_brand_id = last_id + 1
        print(f"생성할 새 브랜드 ID: {new_brand_id}")

        # 없으면 새로 생성
        new_brand = Brand(
            brand_id=new_brand_id,
            subsidiary_id=str(uuid.uuid4()),
            brand_name=brand_data.get("brand_name", None),  # 기본값으로 None
            main_phone_number=None,
            manager_email=brand_data.get("manager_email", None),
            manager_phone_number=None,
            sales_status=None,
            sales_status_note=None,
            category=None,
            core_product_summary=None,
            recent_brand_issues=None,
            last_updated_at=None
        )
        session.add(new_brand)
        await session.flush()  # brand_id 확보
        await session.commit()  # 데이터베이스에 실제 반영
        session.close()
        return new_brand.brand_id

    except SQLAlchemyError as e:
        print(f"❌ 브랜드 저장 중 오류 발생: {e}")
        await session.rollback()
        return None

# 8️⃣ 비동기적으로 MariaDB에 데이터 저장
async def save_to_mariadb_async(fields: dict, session: AsyncSession):
    new_log = SalesLog(
        brand_id=await get_or_create_brand(session, fields),
        brand_name=fields["brand_name"],
        manager_name=fields["manager_name"],
        manager_email=fields["manager_email"],
        agent_name=fields["agent_name"],
        call_full_text=fields["call_full_text"],
        call_memo=fields["call_memo"],
        proposal_url=fields["proposal_url"],
        is_proposal_generated=fields["is_proposal_generated"],
        remarks=fields["remarks"],
        contact_time=fields["contact_time"],
        last_updated_at=fields["last_updated_at"],
        contact_method=fields["contact_method"],
        sales_status=fields["sales_status"],
        client_needs_summary=fields["client_needs_summary"]
    )

    session.add(new_log)
    await session.commit()
    print("✅ [Async] sales_log 테이블에 데이터 저장 완료")
    session.close()

# 9️⃣ 데이터 처리 흐름을 담당하는 함수
def run(state:CallingState):
    # 음성 텍스트 인식
    state = transcribe(state)
    
    # 통화 내용 요약 및 요구사항 정리
    state = summarize(state)
    
    # 요약에서 필드 추출
    return extract_fields(state["summary"], state["full_text"])

