# create_vectorstore.py
import pandas as pd
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np
import os

# BERT 임베딩 클래스 정의
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
        return cls_embedding.cpu().numpy()

def main():
    # CSV 파일 경로
    file_path = "../data/data_sample/media.csv"
    
    # CSV 파일 로드
    df = pd.read_csv(file_path, header=None)
    
    # 컬럼명 정의
    df.columns = [
        "media_id",
        "media_name",
        "location",
        "specification",
        "slot_count",
        "media_type",
        "operating_hours",
        "guaranteed_exposure",
        "duration_seconds",
        "quantity",
        "unit_price",
        "image_day_url",
        "image_night_url",
        "image_map_url",
        "population_target",
        "media_characteristics",
        "case_examples"
    ]
    
    # 문서 생성
    docs = []
    for i, row in df.iterrows():
        doc = Document(
            page_content=f"""
            위치: {row['location']}
            타겟: {row['population_target']}
            매체 특징: {row['media_characteristics']}
            집행 사례: {row['case_examples']}
            """,
            metadata={
                "media_id": str(row["media_id"]),
                "media_name": row["media_name"],
                "location": row["location"],
                "media_type": row["media_type"],
                "population_target": row["population_target"],
                "media_characteristics": row["media_characteristics"],
                "case_examples": row["case_examples"]
            }
        )
        docs.append(doc)
    
    # 임베딩 함수 초기화
    embedding_function = BERTSentenceEmbedding()
    
    # Chroma 벡터스토어 생성 및 저장
    persist_directory = "./chroma_media"
    chroma_collection = Chroma.from_documents(
        documents=docs,
        embedding=embedding_function,
        collection_name="media",
        persist_directory=persist_directory
    )
    
    print(f"벡터스토어가 {persist_directory}에 성공적으로 생성되었습니다.")
    print(f"총 {len(docs)}개의 문서가 저장되었습니다.")

if __name__ == "__main__":
    main()