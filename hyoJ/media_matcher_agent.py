# media_matcher.py
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from models.db_model import Brand, BrandMediaMatch
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import uuid

# BERT 임베딩 클래스 재정의 (쿼리용)
class BERTSentenceEmbedding:
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)

    def embed_documents(self, texts):
        return [self._embed(text) for text in texts]

    def embed_query(self, text):
        return self._embed(text)

    def _embed(self, text):
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
        with torch.no_grad():
            outputs = self.model(**inputs)
        cls_embedding = outputs.last_hidden_state[:, 0, :].squeeze(0)
        return cls_embedding.cpu().numpy().tolist()

def load_vectorstore(persist_directory="../chroma_media", collection_name="media"):
    # 임베딩 함수 초기화 (쿼리용)
    embedding_function = BERTSentenceEmbedding()
    
    # 저장된 Chroma 벡터스토어 로드
    chroma_collection = Chroma(
        collection_name=collection_name,
        embedding_function=embedding_function,
        persist_directory=persist_directory
    )
    
    return chroma_collection

def media_matcher_agent(brand_name, recent_issue, core_product_summary, manager_name, persist_directory="../chroma_media"):
    # LLM 초기화
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # 벡터스토어 로드
    chroma_collection = load_vectorstore(persist_directory)
    
    # 쿼리 텍스트 구성
    query_text = f"{recent_issue} / {core_product_summary}"
    
    # 유사도 검색 수행
    results = chroma_collection.similarity_search_with_score(query_text, k=10)
    
    # 첫 번째 매체만 추출
    top_match = None
    for doc, _ in results:
        meta = doc.metadata
        reason = f"{meta['population_target']}을 타겟으로 하며, '{meta['media_characteristics']}' 특성을 가짐. '{meta['case_examples']}' 등 유사 캠페인 존재."
        top_match = {
            "media_id": meta["media_id"],
            "media_name": meta["media_name"],
            "location": meta["location"],
            "media_type": meta["media_type"],
            "match_reason": reason
        }
        break  # 첫 번째 결과만 사용
    
    # 전화 스크립트 생성
    script_prompt = f"""
    브랜드명: {brand_name}
    최근 마케팅 이슈: {recent_issue}
    브랜드 설명: {core_product_summary}
    추천 매체: {top_match['media_name']} ({top_match['location']}) - {top_match['match_reason']}

    위 정보를 바탕으로, {brand_name}의 담당자에게 전화할 때 사용할 영업 스크립트를 3-5줄로 작성해주세요.
    스크립트는 다음을 포함해야 합니다:
    - 인사 및 자기소개
    - 브랜드의 최근 이슈 언급
    - 추천 매체({top_match['media_name']})가 왜 적합한지 설명
    - 미팅 제안
    
    실제 영업 전화 통화처럼 정중하지만 자연스럽게 작성해주세요.
    """
    sales_call_script = llm.invoke(script_prompt).content.strip()

    # 이메일 생성
    email_prompt = f"""
    브랜드명: {brand_name}
    최근 마케팅 이슈: {recent_issue}
    브랜드 설명: {core_product_summary}
    담당자 이름: {manager_name}
    추천 매체: {top_match['media_name']} ({top_match['location']}) - {top_match['match_reason']}

    위 정보를 바탕으로, 다음 정확한 형식에 맞춰 이메일을 작성해주세요:

    안녕하세요.  
    옥외광고 매체사 <올이즈굿>의 광고팀 {manager_name} 매니저입니다.

    {brand_name}에 적합한 옥외광고인  
    {top_match['media_name']}를 소개해 드리고자 메일을 남기게 되었습니다.

    {{해당 매체 간단 특징}} 다음과 같은 특징을 가지고 있습니다:

    {{해당 매체의 특징 및 왜 {brand_name}에 적합한지 3가지 이유 설명}}

    이외에도 저희 올이즈굿은 올림픽대로 야립광고와 지하철, 버스 등 여러 교통 매체뿐 아니라  
    이태원/강남/명동 등 서울 주요 지역의 옥외 매체를 활용한 마케팅 솔루션을 제공하고 있습니다.

    첨부된 소개서에서 {top_match['media_name']}와 다른 매체들을 함께 확인하실 수 있습니다.  
    확인 후 회신 주시면, 전화나 미팅을 통해 더 자세히 안내해 드리겠습니다 :)

    긴 메일 읽어주셔서 감사합니다.  
    올이즈굿 {manager_name} 드림

    주의사항:
    1. {manager_name} 부분은 실제 값을 사용합니다.
    2. {{해당 매체 간단 특징}} 부분은 {top_match['media_name']}에 대한 간단한 한 줄 설명으로 대체하세요.
    3. {{해당 매체의 특징 및 왜 적합한지 3가지 이유 설명}} 부분은 {top_match['media_name']}의 특징과 {brand_name}에 왜 적합한지 3가지 이유를 번호를 매겨 설명하세요.
    4. 위 형식을 정확히 따라 줄바꿈과 공백도 동일하게 유지하세요.
    """
    proposal_email = llm.invoke(email_prompt).content.strip()

    now = datetime.now()
    formatted = now.strftime("%Y-%m-%d %H:%M:%S")

    # 결과 반환
    return {

        "media_id" : top_match["media_id"],
        "media_name": top_match["media_name"],
        "location": top_match["location"],
        "media_type": top_match["media_type"],
        "match_reason": top_match["match_reason"],

        "sales_call_script": sales_call_script,
        "proposal_email": proposal_email,

        "generated_at" : formatted, 
        "used_in_sales" : False, 
        "last_updated_at" : formatted
    }

async def save_brand_and_media_match(fields: dict, result: dict, session: AsyncSession):
    try:
        brand_name = fields["brand_name"].strip()

        # 1. 브랜드 존재 여부 확인
        stmt = select(Brand).where(Brand.brand_name == brand_name)
        existing_result = await session.execute(stmt)
        existing_brand = existing_result.scalars().first()

        if existing_brand:
            brand_id = existing_brand.brand_id
        else:
            # 새 brand_id 계산
            max_id_stmt = select(func.max(Brand.brand_id))
            max_id_result = await session.execute(max_id_stmt)
            max_brand_id = max_id_result.scalar() or 0
            new_brand_id = max_brand_id + 1

            # 새 브랜드 저장
            new_brand = Brand(
                brand_id=new_brand_id,
                subsidiary_id=str(uuid.uuid4()),
                brand_name=brand_name,
                main_phone_number=None,
                manager_email=None,
                manager_phone_number=None,
                sales_status=fields.get("sales_status"),
                sales_status_note=None,
                category=fields.get("category"),
                core_product_summary=fields["core_product_summary"],
                recent_brand_issues=fields["recent_brand_issues"],
                last_updated_at=datetime.now()
            )
            session.add(new_brand)
            await session.flush()
            await session.refresh(new_brand)
            brand_id = new_brand.brand_id

        # 2. brand_id + media_id 조합 중복 확인
        media_id = result["media_id"]
        stmt = select(BrandMediaMatch).where(
            BrandMediaMatch.brand_id == brand_id,
            BrandMediaMatch.media_id == media_id
        )
        existing_match_result = await session.execute(stmt)
        existing_match = existing_match_result.scalars().first()

        if existing_match:
            print(f"✅ 이미 존재하는 매치 (brand_id: {brand_id}, media_id: {media_id})")
            return existing_match

        # proposal_email 분할
        email_parts = result["proposal_email"].split("\n\n", 2)
        email_part_1 = email_parts[0] if len(email_parts) > 0 else ""
        email_part_2 = email_parts[1] if len(email_parts) > 1 else ""
        email_part_3 = email_parts[2] if len(email_parts) > 2 else ""

        # 새 brand_media_match 저장
        max_match_id_stmt = select(func.max(BrandMediaMatch.id))
        max_match_id_result = await session.execute(max_match_id_stmt)
        max_match_id = max_match_id_result.scalar() or 0
        new_match_id = max_match_id + 1

        new_match = BrandMediaMatch(
            id=new_match_id,
            brand_id=brand_id,
            media_id=media_id,
            match_reason=result["match_reason"],
            sales_call_script=result["sales_call_script"],
            proposal_email_part_1=email_part_1,
            proposal_email_part_2=email_part_2,
            proposal_email_part_3=email_part_3,
            generated_at=datetime.strptime(result["generated_at"], "%Y-%m-%d %H:%M:%S"),
            used_in_sales=result["used_in_sales"],
            last_updated_at=datetime.strptime(result["last_updated_at"], "%Y-%m-%d %H:%M:%S"),
        )

        session.add(new_match)
        await session.flush()
        await session.refresh(new_match)
        await session.commit()

        print(f"✅ 저장 완료: brand_id={brand_id}, media_id={media_id}")
        return new_match

    except SQLAlchemyError as e:
        print(f"❌ 오류 발생: {e}")
        await session.rollback()
        return None