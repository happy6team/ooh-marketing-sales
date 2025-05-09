import asyncio
from AgentState import AgentState
from langchain_openai import ChatOpenAI
from brand_explorer_agent import brand_explorer_agent
from media_matcher_agent import media_matcher_agent
from main import save_brands, save_media_matchers
from db import AsyncSessionLocal


import pandas as pd

async def run_company_media_agent_async(category, time_filter, manager_name):
    try:
        async with AsyncSessionLocal() as session:

            state = AgentState(
            brand_list=[],
            recent_brand_issues=[],
            core_product_summary=[],
            category=category,
            time_filter=time_filter,
            manager_name=manager_name
            )

            result = brand_explorer_agent(state)
            await save_brands(result, session=session)

            df = pd.DataFrame(result)

            df['matched_media'] = None
            df['media_location'] = None
            df['media_type'] = None
            df['match_reason'] = None
            df['sales_call_script'] = None
            df['proposal_email'] = None

            for i in range(df.shape[0]):
                brand_name = df.loc[i, 'brand_list']
                recent_issue = df.loc[i, 'recent_brand_issues']
                core_product_summary = df.loc[i, 'core_product_summary']

                match_data = media_matcher_agent(
                    brand_name, recent_issue, core_product_summary,
                    manager_name, persist_directory="./chroma_media"
                )

                await save_media_matchers({
                    "brand_name": brand_name,
                    "category": category,
                    "core_product_summary": core_product_summary,
                    "recent_brand_issues": recent_issue
                }, match_data, session)

                df.loc[i, 'matched_media'] = match_data['media_name']
                df.loc[i, 'media_location'] = match_data['location']
                df.loc[i, 'media_type'] = match_data['media_type']
                df.loc[i, 'match_reason'] = match_data['match_reason']
                df.loc[i, 'sales_call_script'] = match_data['sales_call_script']
                df.loc[i, 'proposal_email'] = match_data['proposal_email']
        return df
    except RuntimeError as e:
        if "attached to a different loop" in str(e):
            print("이벤트 루프 오류 발생. 세션을 안전하게 종료합니다.")
            # 필요한 정리 작업 수행
    

# Streamlit 또는 다른 일반 코드에서 실행
def run_company_media_agent(category, time_filter, manager_name):
    try:
        loop = asyncio.get_running_loop()
        return loop.run_until_complete(run_company_media_agent_async(category, time_filter, manager_name))
    except RuntimeError:
        return asyncio.run(run_company_media_agent_async(category, time_filter, manager_name))
