import streamlit as st
import pandas as pd
from datetime import datetime


# 페이지 설정
st.set_page_config(page_title="영업 자동화 대시보드", layout="wide")

# 사이드바 설정
st.sidebar.title("영업 자동화 필터")

# 담당자 선택
담당자_options = ["손지영", "진실", "이효정"]
selected_담당자 = st.sidebar.selectbox("담당자 선택", 담당자_options, index=0)

# 카테고리 선택
카테고리_options = [
    "패션", "뷰티", "식음료", "전자제품", 
    "인테리어", "건강", "레저", "이커머스", "금융"
]
selected_카테고리 = st.sidebar.selectbox("카테고리 선택", 카테고리_options, index=0)

# 날짜 선택
date_range = st.sidebar.date_input(
    "날짜 범위", 
    value=(datetime.now().date(), datetime.now().date())
)

# 메인 콘텐츠 영역
st.title("영업 자동화 대시보드")


if st.button("기업 정보 업데이트"):
    st.write("기업 정보를 업데이트합니다...")
    

