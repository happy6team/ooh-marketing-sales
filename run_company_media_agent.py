from AgentState import AgentState
from langchain_openai import ChatOpenAI

from brand_explorer_agent import brand_explorer_agent
from media_matcher_agent import media_matcher_agent


import pandas as pd


def run_company_media_agent(category, time_filter, manager_name):

    # llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    state = AgentState(
        brand_list=[],
        recent_brand_issues=[],
        core_product_summary=[],
        category=category, 
        time_filter=time_filter,
        manager_name=manager_name
    )

    result = brand_explorer_agent(state)

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

        # match_data = media_matcher_agent(brand_name, recent_issue, core_product_summary)

        match_data = media_matcher_agent(brand_name, recent_issue, core_product_summary, manager_name, persist_directory="./chroma_media")
        
        df.loc[i, 'matched_media'] = match_data['media_name']
        df.loc[i, 'media_location'] = match_data['location']
        df.loc[i, 'media_type'] = match_data['media_type']
        df.loc[i, 'match_reason'] = match_data['match_reason']
        df.loc[i, 'sales_call_script'] = match_data['sales_call_script']
        df.loc[i, 'proposal_email'] = match_data['proposal_email']

    return df