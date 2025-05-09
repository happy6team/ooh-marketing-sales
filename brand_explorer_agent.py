from langchain_openai import ChatOpenAI
from AgentState import AgentState
from langchain_teddynote.tools.tavily import TavilySearch
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage
from datetime import datetime
import ast
import re
from dotenv import load_dotenv
load_dotenv()

search_tool = TavilySearch()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def brand_explorer_agent(state: AgentState) -> AgentState:
    """
    패션 브랜드의 최신 마케팅 이슈를 탐색하는 에이전트
    """
    category = state["category"]
    time_filter = state["time_filter"]

    # 더 다양한 결과를 위해 여러 검색 쿼리 실행
    search_queries = [
        f"국내 {category} 브랜드 {time_filter} 팝업스토어 이슈 뉴스",
        f"국내 {category} 브랜드 {time_filter} 신제품 출시 이슈",
        f"{category} 브랜드 {time_filter} 앰배서더 광고모델 발표",
        f"{category} 브랜드 {time_filter} 콜라보레이션 협업"
    ]
    
    # 각 쿼리 결과 합치기
    all_web_content = ""
    for query in search_queries:
        result = search_tool.invoke({"query": query})
        result_str = str(result)
        all_web_content += result_str + "\n\n=== 다음 검색 결과 ===\n\n"
    
    # 프롬프트 템플릿 생성
    prompt_template = PromptTemplate.from_template(""" 
    당신은 전문 브랜드 분석가입니다.
    
    다음 웹 검색 결과에서 한국 내에서 발생한 {category} 분야의 최신 마케팅 이슈가 있는 브랜드를 최대 10개까지 추출해주세요.
    
    반드시 아래와 같은 구체적인 한국 내 마케팅 이슈가 있는 브랜드만 추출하세요:
    - 한국에서의 신제품 출시
    - 앰배서더 또는 광고 모델 발표
    - 한국 내 팝업스토어 오픈 (서울, 부산 등 국내 도시에서 진행)
    - 브랜드/인물과의 콜라보레이션
    - 한국 소비자를 대상으로 한 마케팅 캠페인

    중요: 반드시 정식 패션 브랜드만 포함해야 합니다. 다음 기준을 만족해야 합니다:
    - 의류, 신발, 액세서리 등을 생산/판매하는 패션 브랜드여야 함
    - 실제 존재하는 패션 브랜드여야 함
    - 게임 캐릭터, 연예인, 아이돌, 가상 인물은 제외
    - 패션 브랜드가 아닌 팝업스토어 주최자는 제외

    반드시 다음 조건을 준수하세요:
    1. 실제 검색 결과에서 확인된 최신 이슈만 포함하세요.
    2. 각 브랜드마다 최대한 서로 다른 날짜의 이슈를 찾으세요. 
    3. 날짜를 찾을 수 없는 경우 '날짜 미상'이라고 표시하고, 절대로 임의의 날짜를 생성하지 마세요.
    4. 실제 마케팅 이슈가 있는 브랜드와 이슈만 포함하고, 없는 내용은 생성하지 마세요.
    5. 최대한 다양한 유형의 이슈(팝업스토어, 콜라보레이션, 신제품 출시 등)를 포함하세요.
    
    다음 형식으로 Python 딕셔너리 리스트를 반환해주세요:
    [
        {{
            "name": "브랜드명", 
            "issue": "이슈 발생 날짜 + 한국 내 발생한 브랜드 이슈 내용 (예: '2025년 5월 1일: 서울 가로수길에 팝업스토어 오픈', '날짜 미상: 새 앰배서더 발표')",
            "description": "브랜드 특징, 주요 제품 라인, 타겟 고객층에 대한 설명"
        }}
    ]
    
    참고: 검색 결과에서 실제로 찾을 수 있는 구체적인 이슈와 날짜만 사용하세요.
    설명 없이 위 형식의 유효한 Python 딕셔너리 리스트만 반환하세요. 코드 블록(```)을 사용하지 마세요.
    
    검색 결과:
    {web_content}
    """)
    
    # 프롬프트 생성 및 LLM 호출
    prompt = prompt_template.format(category=category, time_filter=time_filter, web_content=all_web_content)
    response = llm([HumanMessage(content=prompt)])
    
    try:
        # 응답에서 코드 블록 제거 (있는 경우)
        content = response.content
        if "```" in content:
            pattern = r"```(?:python)?\s*([\s\S]*?)```"
            matches = re.findall(pattern, content)
            if matches:
                content = matches[0].strip()
            else:
                content = content.replace("```python", "").replace("```", "").strip()
        
        # 응답 파싱
        brand_data = ast.literal_eval(content)

        # 리스트가 아니면 오류 처리
        if not isinstance(brand_data, list):
            raise ValueError("응답이 리스트가 아님")

        # 결과 분리하여 준비
        brand_names = [item["name"] for item in brand_data]
        recent_brand_issues = [item["issue"] for item in brand_data]
        core_product_summarys = [item["description"] for item in brand_data]

    except Exception as e:
        print(f"⚠️ 응답 파싱 실패: {e}")
        print(f"원본 응답: {response.content}")
        # 오류 발생 시 빈 리스트 반환
        brand_names = []
        recent_brand_issues = []
        core_product_summarys = []

    now = datetime.now()
    formatted = now.strftime("%Y-%m-%d %H:%M:%S")

    # 결과 업데이트
    return AgentState(
        brand_list=brand_names,
        recent_brand_issues=recent_brand_issues,
        core_product_summary=core_product_summarys,
        sales_status="미접촉", 
        category=category, 
        last_updated_at=formatted
    )
