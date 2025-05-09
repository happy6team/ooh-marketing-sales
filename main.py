# main.py
from fastapi import FastAPI, Depends
from db import AsyncSessionLocal
from loaders.data_loader import load_all_data
from db import init_db, get_db

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    try:
        await init_db() # 테이블 생성
        async with AsyncSessionLocal() as session:
            await load_all_data(session) # 데이터 로드
    except Exception as e:
        import logging
        logging.exception("Startup data loading failed")
        raise e

from sqlalchemy.ext.asyncio import AsyncSession
from hyoJ.call_summary_agent_proto import CallingState, run, save_to_mariadb_async
@app.get("/process_call_data")
async def process_call_data_prototype(session: AsyncSession = Depends(get_db)):
    state = CallingState(
        full_text="",
        summary="",
        messages=[]  # 예시로 빈 리스트로 설정
    )

    # run 함수 실행하여 결과 얻기
    fields = run(state)

    # 비동기적으로 MariaDB에 데이터 저장
    await save_to_mariadb_async(fields, session)

    return {"message": "Call data processed and saved successfully"}


from AgentState import AgentState
from hyoJ.brand_explorer_agent_proto import brand_explorer_agent, save_brands_to_mariadb  # 에이전트 로직
 
@app.get("/process_brands")
async def process_brands_prototype(session: AsyncSession = Depends(get_db)):
    # 👉 에이전트에 전달할 입력 상태 설정
    state = AgentState(
        category="패션",           # 또는 요청 파라미터로 받을 수도 있음
        time_filter="최근 1개월"  # 예시 필터
    )

    # 1. 브랜드 이슈 탐색
    fields = brand_explorer_agent(state)

    # 2. MariaDB에 저장
    saved = await save_brands_to_mariadb(fields, session)

    return {
        "message": "브랜드 데이터 처리 및 저장 완료",
        "saved_count": len(saved) if saved else 0,
        "brand_names": fields["brand_list"]
    }

from hyoJ.media_matcher_agent_proto import media_matcher_agent, save_brand_and_media_match

@app.get("/match_media")
async def match_media_prototype(session: AsyncSession = Depends(get_db)):
    
    fields = {
        "brand_list": ["브랜드1", "브랜드2", "브랜드3"],
        "category": ["패션", "패션", "패션"],  # 브랜드별 카테고리
        "recent_brand_issues": [
            "브랜드1 관련 최근 이슈",
            "브랜드2 관련 최근 이슈",
            "브랜드3 관련 최근 이슈"
        ],
            "core_product_summary": [
            "브랜드1의 고급스러운 디자인 아이템",
            "브랜드2의 유니크한 트렌디 아이템",
            "브랜드3의 실용적인 기능성 아이템"
        ]
    }

    manager_name = "손지영"

    saved_matches = []

    for i in range(len(fields["brand_list"])):
        brand_name = fields["brand_list"][i]
        category = fields["category"][i]
        recent_issue = fields["recent_brand_issues"][i]
        core_product_summary = fields["core_product_summary"][i]

        media_result = media_matcher_agent(
            brand_name=brand_name,
            recent_issue=recent_issue,
            core_product_summary=core_product_summary,
            manager_name=manager_name
        )

        save_result = await save_brand_and_media_match(
            {
                "brand_name": brand_name,
                "category": category,
                "core_product_summary": core_product_summary,
                "recent_brand_issues": recent_issue
            },
            media_result,
            session
        )
        saved_matches.append(save_result)

    return {
        "message": "미디어 매칭 저장 완료",
        "matched_count": sum(1 for r in saved_matches if r),
        "matched_brand_names": fields["brand_list"]
    }

# ------

async def save_brands(fields: dict, session: AsyncSession):
    await save_brands_to_mariadb(fields, session)

async def save_media_matchers(fields: dict, media_fields: dict, session: AsyncSession):
    await save_brand_and_media_match(fields, media_fields, session)