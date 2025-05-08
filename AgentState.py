from typing import Annotated, TypedDict

class AgentState(TypedDict):
    brand_list: Annotated[list[str], "brand_list"] 
    brand_issue: Annotated[list[str], "brand_issue"] 
    brand_description: Annotated[list[str], "brand_description"] 

    category: str
    time_filter: str
    manager_name: str