from faster_whisper import WhisperModel
import openai
import re
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, Any

# 환경 변수 로드
load_dotenv()

def call_summary_agent(brand_name: str, manager_name: str, manager_email: str = None) -> Dict[str, Any]:
    """
    음성 통화 데이터를 분석하고 요약하는 에이전트
    
    Args:
        brand_name: 브랜드 이름
        manager_name: 담당자 이름
        manager_email: 담당자 이메일 (옵션)
    
    Returns:
        요약된 통화 내용과 정보가 포함된 딕셔너리
    """
    # 1. 음성 인식 수행
    model = WhisperModel("base")
    segments, info = model.transcribe("./data/audio_sample/calling_data.wav")
    full_text = " ".join([seg.text for seg in segments])
    
    # 2. 텍스트 요약 수행
    client = openai.OpenAI()
    
    prompt = f"""
    다음 {brand_name} 담당자 {manager_name}과의 통화 내용을 요약하고, 
    고객의 요구사항을 다음 필드별로 정리해줘:
    
    - 요구사항 요약:
    - 영업 상태: (관심 있음, 검토 중, 긍정적, 부정적 등의 상태 중 하나로)
    - 비고:
    - 통화 1줄 요약:
    - 지역:
    - 매체:
    - 타겟층:

    통화 내용:
    \"\"\"{full_text}\"\"\"  
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
    
    # 3. 필드 추출
    def extract(label):
        match = re.search(f"{label}: *(.*)", summary)
        return match.group(1).strip() if match else None
    
    # 주요 필드 추출
    client_needs = extract("요구사항 요약")
    sales_status = extract("영업 상태")
    remarks = extract("비고")
    call_summary = extract("통화 1줄 요약")
    region = extract("지역")
    media = extract("매체")
    target = extract("타겟층")
    
    # 요구사항 요약 구성
    summary_parts = []
    if region:
        summary_parts.append(f"{region}")
    if media:
        summary_parts.append(f"{media}")
    if target:
        summary_parts.append(f"{target}")
    client_needs_summary = ", ".join(summary_parts) if summary_parts else client_needs
    
    # 4. 결과 반환
    return {
        "brand_name": brand_name,
        "manager_name": manager_name,
        "manager_email": manager_email,
        "call_full_text": full_text,
        "call_summary": call_summary,
        "client_needs_summary": client_needs_summary,
        "sales_status": sales_status or "검토 중",  # 기본값
        "remarks": remarks,
        "contact_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }