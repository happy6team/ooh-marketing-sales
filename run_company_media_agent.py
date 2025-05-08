from AgentState import AgentState
from langchain_openai import ChatOpenAI

from brand_explorer_agent import brand_explorer_agent
from media_matcher_agent import media_matcher_agent


import pandas as pd


def run_company_media_agent(category, time_filter, manager_name):

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    state = AgentState(
        brand_list=[],
        brand_issue=[],
        brand_description=[],
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
        recent_issue = df.loc[i, 'brand_issue']
        brand_description = df.loc[i, 'brand_description']

        # match_data = media_matcher_agent(brand_name, recent_issue, brand_description)

        match_data = media_matcher_agent(brand_name, recent_issue, brand_description, manager_name, persist_directory="./chroma_media")
        
        df.loc[i, 'matched_media'] = match_data['top_match']['media_name']
        df.loc[i, 'media_location'] = match_data['top_match']['location']
        df.loc[i, 'media_type'] = match_data['top_match']['media_type']
        df.loc[i, 'match_reason'] = match_data['top_match']['match_reason']
        df.loc[i, 'sales_call_script'] = match_data['sales_call_script']
        df.loc[i, 'proposal_email'] = match_data['proposal_email']

    return df