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
from prototype import CallingState, run, save_to_mariadb_async
@app.get("/process_call_data")
async def process_call_data(session: AsyncSession = Depends(get_db)):
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
from brand_explorer_agent import brand_explorer_agent, save_brands_to_mariadb  # 에이전트 로직
 
@app.get("/process_brands")
async def process_brands(session: AsyncSession = Depends(get_db)):
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

from media_matcher_agent import media_matcher_agent, save_brand_and_media_match

@app.get("/match_media")
async def match_media(session: AsyncSession = Depends(get_db)):
    
    fields = {
        "brand_list": ["브랜드1", "브랜드2", "브랜드3"],  # 예시 브랜드 목록
        "category": "패션",  # 예시 카테고리
        "recent_brand_issues": "최근 1개월 동안 주목받은 패션 트렌드",  # 최근 브랜드 이슈
        "core_product_summary": "고급스러운 디자인의 패션 아이템들",  # 핵심 제품 요약
    }
    
    manager_name = "김이사"  # 예시. 실제 운영 시 auth 정보에서 가져오거나 request로 받기
    saved_matches = []

    # fields에서 brand_names 등을 가져옴
    for brand_name in fields["brand_list"]:
        media_result = media_matcher_agent(
            brand_name=brand_name,
            recent_issue=fields["recent_brand_issues"],
            core_product_summary=fields["core_product_summary"],
            manager_name=manager_name
        )

        save_result = await save_brand_and_media_match(
            {
                "brand_name": brand_name,
                "category": fields["category"],
                "core_product_summary": fields["core_product_summary"],
                "recent_brand_issues": fields["recent_brand_issues"]
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